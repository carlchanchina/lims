# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now


def _contact_names_for_customer(customer):
	return frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"link_doctype": "Customer",
			"link_name": customer,
		},
		pluck="parent",
	)


def _customer_names_for_contact(contact):
	return frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"parent": contact,
			"link_doctype": "Customer",
		},
		pluck="link_name",
	)


def sync_customer(doc, method=None, *args, **kwargs):
	"""ERPNext Customer -> LIMS Customer(含联系人子表)。"""
	upsert_lims_customer(doc.name)


def sync_contact(doc, method=None, *args, **kwargs):
	"""ERPNext Contact -> LIMS Contact,并刷新关联客户。"""
	upsert_lims_contact(doc.name)
	for customer in _customer_names_for_contact(doc.name):
		upsert_lims_customer(customer)


def delete_customer(doc, method=None, *args, **kwargs):
	if frappe.db.exists("LIMS Customer", doc.name):
		frappe.delete_doc("LIMS Customer", doc.name, force=1, ignore_permissions=True)
	for contact in _contact_names_for_customer(doc.name):
		upsert_lims_contact(contact)


def delete_contact(doc, method=None, *args, **kwargs):
	customers = _customer_names_for_contact(doc.name)
	if frappe.db.exists("LIMS Contact", doc.name):
		frappe.delete_doc("LIMS Contact", doc.name, force=1, ignore_permissions=True)
	for customer in customers:
		upsert_lims_customer(customer)


def rename_customer(doc, method=None, old=None, new=None, *args, **kwargs):
	if old and new and frappe.db.exists("LIMS Customer", old):
		frappe.rename_doc("LIMS Customer", old, new, force=True, ignore_permissions=True)
		upsert_lims_customer(new)


def rename_contact(doc, method=None, old=None, new=None, *args, **kwargs):
	if old and new and frappe.db.exists("LIMS Contact", old):
		frappe.rename_doc("LIMS Contact", old, new, force=True, ignore_permissions=True)
	upsert_lims_contact(new or doc.name)


def upsert_lims_customer(customer_name):
	if not customer_name or not frappe.db.exists("Customer", customer_name):
		return
	customer = frappe.get_doc("Customer", customer_name)
	lims = (
		frappe.get_doc("LIMS Customer", customer.name)
		if frappe.db.exists("LIMS Customer", customer.name)
		else frappe.new_doc("LIMS Customer")
	)
	lims.customer = customer.name
	lims.customer_name = customer.customer_name
	lims.customer_group = customer.customer_group
	lims.territory = customer.territory
	lims.customer_type = customer.customer_type
	lims.default_price_list = customer.default_price_list
	lims.status = "停用" if customer.disabled else "启用"
	lims.last_synced = now()

	lims.set("contacts", [])
	for contact_name in _contact_names_for_customer(customer.name):
		contact = frappe.db.get_value(
			"Contact",
			contact_name,
			["full_name", "email_id", "phone", "designation", "is_primary_contact"],
			as_dict=True,
		)
		if not contact:
			continue
		lims.append(
			"contacts",
			{
				"contact": contact_name,
				"full_name": contact.full_name,
				"email_id": contact.email_id,
				"phone": contact.phone,
				"designation": contact.designation,
				"is_primary": contact.is_primary_contact,
			},
		)

	lims.flags.ignore_permissions = True
	lims.save(ignore_permissions=True)


def upsert_lims_contact(contact_name):
	if not contact_name or not frappe.db.exists("Contact", contact_name):
		return
	contact = frappe.get_doc("Contact", contact_name)
	lims = (
		frappe.get_doc("LIMS Contact", contact.name)
		if frappe.db.exists("LIMS Contact", contact.name)
		else frappe.new_doc("LIMS Contact")
	)
	lims.contact = contact.name
	lims.full_name = contact.full_name
	lims.email_id = contact.email_id
	lims.mobile_no = contact.mobile_no
	lims.phone = contact.phone
	lims.designation = contact.designation
	lims.company_name = contact.company_name
	lims.last_synced = now()

	lims.set("customers", [])
	for customer in _customer_names_for_contact(contact.name):
		lims.append(
			"customers",
			{
				"customer": customer,
				"customer_name": frappe.db.get_value(
					"Customer", customer, "customer_name"
				),
			},
		)

	lims.flags.ignore_permissions = True
	lims.save(ignore_permissions=True)


def backfill_parties():
	"""全量同步 ERPNext Customer / Contact 到 LIMS 镜像表。"""
	for customer in frappe.get_all("Customer", pluck="name"):
		upsert_lims_customer(customer)
	for contact in frappe.get_all("Contact", pluck="name"):
		upsert_lims_contact(contact)
