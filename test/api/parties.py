# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def list_customers(txt=None):
	"""读取同步自 ERPNext 的 LIMS Customer 镜像。"""
	require_roles(ALL_STAFF_ROLES)
	or_filters = None
	if txt:
		or_filters = [
			["customer", "like", f"%{txt}%"],
			["customer_name", "like", f"%{txt}%"],
		]
	return frappe.get_list(
		"LIMS Customer",
		or_filters=or_filters,
		fields=["name", "customer", "customer_name", "status", "default_price_list"],
		order_by="customer_name asc",
		limit_page_length=50,
	)


@frappe.whitelist()
def get_customer(name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc("LIMS Customer", name).as_dict()


@frappe.whitelist()
def list_contacts(customer=None):
	require_roles(ALL_STAFF_ROLES)
	if customer:
		names = frappe.get_all(
			"LIMS Contact Customer",
			filters={"customer": customer},
			pluck="parent",
		)
		if not names:
			return []
		return frappe.get_all(
			"LIMS Contact",
			filters={"name": ["in", names]},
			fields=["name", "contact", "full_name", "email_id", "mobile_no", "designation"],
			order_by="full_name asc",
		)
	return frappe.get_all(
		"LIMS Contact",
		fields=["name", "contact", "full_name", "email_id", "mobile_no", "designation"],
		order_by="full_name asc",
		limit_page_length=100,
	)
