# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_manager, require_roles


def _list_doctype(doctype, filters=None, page=0, page_length=50, fields=None):
	require_roles(ALL_STAFF_ROLES)
	filters = filters or {}
	return frappe.get_list(
		doctype,
		filters=filters,
		fields=fields or ["name"],
		order_by="modified desc",
		start=int(page or 0),
		page_length=int(page_length or 50),
	)


def _get_doc(doctype, name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc(doctype, name).as_dict()


def _save_doc(doctype, data):
	require_manager()
	name = (data or {}).get("name")
	doc = frappe.get_doc(doctype, name) if name else frappe.new_doc(doctype)
	fields = {
		"standard_code",
		"standard_name",
		"organization",
		"status",
		"version",
		"effective_date",
		"superseded_by",
		"remarks",
		"catalog_code",
		"catalog_name",
		"item",
		"customer",
		"industry",
		"price",
		"uom",
		"tat_days",
		"enabled",
		"industry_name",
	}
	for field in fields & set(data or {}):
		doc.set(field, data[field])
	doc.save(ignore_permissions=False)
	return {"name": doc.name}


@frappe.whitelist()
def get_standards(filters=None, page=0):
	return _list_doctype(
		"Test Standard",
		filters,
		page,
		fields=[
			"name",
			"standard_code",
			"standard_name",
			"version",
			"organization",
			"effective_date",
			"superseded_by",
			"status",
			"remarks",
		],
	)


@frappe.whitelist()
def get_standard(name):
	return _get_doc("Test Standard", name)


@frappe.whitelist()
def save_standard(data):
	return _save_doc("Test Standard", data)


@frappe.whitelist()
def delete_standard(name):
	require_manager()
	if _request_item_uses(name):
		frappe.throw("该标准已被检测请求引用,不能删除")
	frappe.delete_doc("Test Standard", name)
	return {"name": name}


@frappe.whitelist()
def get_industries(filters=None, page=0):
	return _list_doctype(
		"Industry",
		filters,
		page,
		fields=["name", "industry_name", "remarks"],
	)


@frappe.whitelist()
def save_industry(data):
	return _save_doc("Industry", data)


@frappe.whitelist()
def delete_industry(name):
	require_manager()
	if frappe.db.exists("Test Agreement Price", {"industry": name}):
		frappe.throw("该行业已被协议价引用,不能删除")
	if frappe.db.exists("LIMS Customer", {"industry": name}):
		frappe.throw("该行业已被客户引用,不能删除")
	frappe.delete_doc("Industry", name)
	return {"name": name}


@frappe.whitelist()
def get_agreement_prices(filters=None, page=0):
	return _list_doctype(
		"Test Agreement Price",
		filters,
		page,
		fields=[
			"name",
			"catalog_code",
			"catalog_name",
			"item",
			"customer",
			"industry",
			"price",
			"uom",
			"tat_days",
			"enabled",
			"remarks",
		],
	)


@frappe.whitelist()
def get_agreement_price(name):
	return _get_doc("Test Agreement Price", name)


@frappe.whitelist()
def save_agreement_price(data):
	return _save_doc("Test Agreement Price", data)


@frappe.whitelist()
def delete_agreement_price(name):
	require_manager()
	if frappe.db.has_column("Quotation Item", "agreement_price") and frappe.db.exists(
		"Quotation Item", {"agreement_price": name}
	):
		frappe.throw("该协议价已被报价单引用,不能删除,请改为停用(取消勾选启用)")
	frappe.delete_doc("Test Agreement Price", name)
	return {"name": name}


def _request_item_uses(standard):
	rows = frappe.get_all(
		"Test Request Item",
		filters={"standard": standard},
		fields=["parent"],
	)
	for row in rows:
		status = frappe.db.get_value("Test Request", row.parent, "status")
		if status in ("草稿", "已报价", "待检测", "检测中"):
			return True
	return False
