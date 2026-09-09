# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_manager, require_roles


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
		"remarks",
		"equipment_code",
		"equipment_name",
		"model",
		"catalog_code",
		"catalog_name",
		"item",
		"standard",
		"equipment",
		"price",
		"uom",
		"tat_days",
		"is_default",
		"enabled",
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
		fields=["name", "standard_code", "standard_name", "organization", "status", "remarks"],
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
	if frappe.db.exists("Test Catalog", {"standard": name}):
		frappe.throw("该标准已被 Test Catalog 引用,请先停用/移除引用")
	if _request_item_uses(name):
		frappe.throw("该标准已被检测请求引用,不能删除")
	frappe.delete_doc("Test Standard", name)
	return {"name": name}


@frappe.whitelist()
def get_equipment_list(filters=None, page=0):
	return _list_doctype(
		"Equipment",
		filters,
		page,
		fields=["name", "equipment_code", "equipment_name", "model", "status", "remarks"],
	)


@frappe.whitelist()
def get_equipment(name):
	return _get_doc("Equipment", name)


@frappe.whitelist()
def save_equipment(data):
	return _save_doc("Equipment", data)


@frappe.whitelist()
def delete_equipment(name):
	require_manager()
	if frappe.db.exists("Test Catalog", {"equipment": name}):
		frappe.throw("该设备已被 Test Catalog 引用,不能删除")
	frappe.delete_doc("Equipment", name)
	return {"name": name}


@frappe.whitelist()
def get_catalog_list(filters=None, page=0):
	return _list_doctype(
		"Test Catalog",
		filters,
		page,
		fields=[
			"name",
			"catalog_code",
			"catalog_name",
			"item",
			"standard",
			"equipment",
			"price",
			"uom",
			"tat_days",
			"is_default",
			"enabled",
			"remarks",
		],
	)


@frappe.whitelist()
def get_catalog(name):
	return _get_doc("Test Catalog", name)


@frappe.whitelist()
def save_catalog(data):
	return _save_doc("Test Catalog", data)


@frappe.whitelist()
def set_default_catalog(name):
	require_manager()
	catalog = frappe.get_doc("Test Catalog", name)
	frappe.db.set_value(
		"Test Catalog",
		{"item": catalog.item, "standard": catalog.standard, "enabled": 1},
		"is_default",
		0,
	)
	frappe.db.set_value("Test Catalog", name, "is_default", 1)
	return {"name": name}


@frappe.whitelist()
def delete_catalog(name):
	require_manager()
	catalog = frappe.get_doc("Test Catalog", name)
	if _request_item_uses(catalog.standard):
		frappe.throw("该目录对应的 item+standard 已被检测请求引用,不能删除")
	frappe.delete_doc("Test Catalog", name)
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
