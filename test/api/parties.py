# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles
from test.integrations.erpnext_masters import create_contact as create_erpnext_contact
from test.integrations.erpnext_masters import create_customer as create_erpnext_customer
from test.integrations.erpnext_masters import default_customer_group, default_territory
from test.integrations.erpnext_party import upsert_lims_contact, upsert_lims_customer


def _as_dict(value):
	if isinstance(value, str):
		return frappe.parse_json(value) or {}
	return value or {}


def _customer_option(name):
	row = frappe.db.get_value(
		"LIMS Customer", name, ["name", "customer", "customer_name"], as_dict=True
	)
	if not row:
		return {"name": name, "value": name, "label": name}
	return {
		"name": row.name,
		"value": row.name,
		"label": f"{row.name} - {row.customer_name}".strip(" -"),
	}


def _contact_option(name):
	row = frappe.db.get_value(
		"LIMS Contact", name, ["name", "full_name", "email_id"], as_dict=True
	)
	if not row:
		return {"name": name, "value": name, "label": name}
	label = row.full_name or row.email_id or row.name
	if row.email_id and row.full_name:
		label = f"{row.full_name} ({row.email_id})"
	return {"name": row.name, "value": row.name, "label": label}


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


@frappe.whitelist()
def search_contacts(txt=None, customer=None):
	"""搜索 ERPNext Contact,给"选已有联系人"用;可按客户过滤。"""
	require_roles(ALL_STAFF_ROLES)
	txt = (txt or "").strip()
	or_filters = None
	if txt:
		or_filters = [
			["full_name", "like", f"%{txt}%"],
			["email_id", "like", f"%{txt}%"],
			["name", "like", f"%{txt}%"],
		]
	fields = ["name", "full_name", "email_id", "mobile_no", "designation"]

	if customer:
		names = frappe.get_all(
			"Dynamic Link",
			filters={
				"parenttype": "Contact",
				"link_doctype": "Customer",
				"link_name": customer,
			},
			pluck="parent",
		)
		if not names:
			return []
		return frappe.get_all(
			"Contact",
			filters={"name": ["in", names]},
			or_filters=or_filters,
			fields=fields,
			order_by="full_name asc",
			limit_page_length=50,
		)

	return frappe.get_all(
		"Contact",
		or_filters=or_filters,
		fields=fields,
		order_by="full_name asc",
		limit_page_length=50,
	)


@frappe.whitelist()
def create_customer(data=None):
	"""新建客户:先写 ERPNext Customer,再刷新 LIMS 镜像,返回可直接选中的值。"""
	require_roles(ALL_STAFF_ROLES)
	payload = _as_dict(data)
	name = create_erpnext_customer(payload)
	upsert_lims_customer(name)
	if payload.get("industry"):
		# 行业是 LIMS 侧的维度(用于匹配行业协议价),不写回 ERPNext。
		frappe.db.set_value("LIMS Customer", name, "industry", payload["industry"])
	for contact in frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"link_doctype": "Customer",
			"link_name": name,
		},
		pluck="parent",
	):
		upsert_lims_contact(contact)
	return _customer_option(name)


@frappe.whitelist()
def create_industry(data=None):
	"""新建行业主数据,协议价与客户都用这个维度。"""
	require_roles(ALL_STAFF_ROLES)
	payload = _as_dict(data)
	industry_name = (payload.get("industry_name") or "").strip()
	if not industry_name:
		frappe.throw("请填写行业名称")
	if frappe.db.exists("Industry", industry_name):
		frappe.throw(f"行业「{industry_name}」已存在,请直接选择")

	doc = frappe.new_doc("Industry")
	doc.industry_name = industry_name
	doc.remarks = payload.get("remarks")
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "value": doc.name, "label": doc.name}


@frappe.whitelist()
def create_contact(data=None):
	"""新建联系人:先写 ERPNext Contact,再刷新 LIMS 镜像。"""
	require_roles(ALL_STAFF_ROLES)
	name = create_erpnext_contact(_as_dict(data))
	upsert_lims_contact(name)
	customer = _as_dict(data).get("customer")
	if customer:
		upsert_lims_customer(customer)
	return _contact_option(name)


@frappe.whitelist()
def party_form_options():
	"""新建客户/联系人表单要用的下拉项与默认值。"""
	require_roles(ALL_STAFF_ROLES)
	return {
		"customer_types": ["Company", "Individual", "Partnership"],
		"industries": frappe.get_all(
			"Industry", fields=["name"], order_by="name", limit_page_length=200
		),
		"customer_groups": frappe.get_all(
			"Customer Group", fields=["name"], order_by="name", limit_page_length=200
		),
		"territories": frappe.get_all(
			"Territory", fields=["name"], order_by="name", limit_page_length=200
		),
		"defaults": {
			"customer_group": default_customer_group(),
			"territory": default_territory(),
		},
	}
