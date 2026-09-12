# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_roles
from lims.integrations.erpnext_masters import create_contact as create_erpnext_contact
from lims.integrations.erpnext_masters import create_customer as create_erpnext_customer
from lims.integrations.erpnext_masters import default_customer_group, default_territory


def _as_dict(value):
	if isinstance(value, str):
		return frappe.parse_json(value) or {}
	return value or {}


def _customer_option(name):
	row = frappe.db.get_value(
		"Customer", name, ["name", "customer_name"], as_dict=True
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
		"Contact", name, ["name", "first_name", "last_name", "email_id"], as_dict=True
	)
	if not row:
		return {"name": name, "value": name, "label": name}
	full_name = " ".join(filter(None, [row.first_name, row.last_name]))
	label = full_name or row.email_id or row.name
	if row.email_id and full_name:
		label = f"{full_name} ({row.email_id})"
	return {"name": row.name, "value": row.name, "label": label}


@frappe.whitelist()
def list_customers(txt=None):
	"""直接读 ERPNext Customer(LIMS 不维护镜像,ERPNext 为唯一事实源)。"""
	require_roles(ALL_STAFF_ROLES)
	filters = {}
	if txt:
		filters["customer_name"] = ["like", f"%{txt}%"]
	return frappe.get_list(
		"Customer",
		filters=filters,
		fields=[
			"name",
			"customer_name",
			"customer_group",
			"territory",
			"default_price_list",
			"disabled",
		],
		order_by="customer_name asc",
		limit_page_length=50,
	)


@frappe.whitelist()
def get_customer(name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc("Customer", name).as_dict()


@frappe.whitelist()
def list_contacts(customer=None):
	"""直接读 ERPNext Contact;可按客户过滤(通过 Contact 的 Dynamic Link)。"""
	require_roles(ALL_STAFF_ROLES)
	fields = [
		"name",
		"full_name",
		"email_id",
		"mobile_no",
		"designation",
	]
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
			fields=fields,
			order_by="name asc",
			limit_page_length=100,
		)
	return frappe.get_all(
		"Contact",
		fields=fields,
		order_by="name asc",
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
	"""新建客户:直接写 ERPNext Customer(含税号、企业性质、行业等定制字段)。"""
	require_roles(ALL_STAFF_ROLES)
	payload = _as_dict(data)
	name = create_erpnext_customer(payload)
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
	"""新建联系人:直接写 ERPNext Contact(可挂到客户)。"""
	require_roles(ALL_STAFF_ROLES)
	return _contact_option(create_erpnext_contact(_as_dict(data)))


@frappe.whitelist()
def party_form_options():
	"""新建客户/联系人表单要用的下拉项与默认值。"""
	require_roles(ALL_STAFF_ROLES)
	return {
		"customer_types": ["Company", "Individual", "Partnership"],
		"industries": frappe.get_all(
			"Industry", fields=["name"], order_by="name", limit_page_length=200
		),
		"enterprise_natures": [
			"军工集团",
			"国有企业",
			"民营企业",
			"外资企业",
			"高校与科研院所",
			"政府机构",
			"事业单位",
			"其他",
		],
		"customer_tiers": ["战略客户", "重点客户", "普通客户", "潜在客户"],
		"contact_roles": ["商务", "技术", "财务", "收样", "管理层", "其他"],
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
