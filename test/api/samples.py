# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


def _require_editable_request(test_request):
	status = frappe.db.get_value("Test Request", test_request, "status")
	if status in ("已完成", "已取消"):
		frappe.throw("请求已结束,不能再维护样品")


@frappe.whitelist()
def list_by_request(test_request):
	require_roles(ALL_STAFF_ROLES)
	if not test_request:
		return []
	return frappe.get_all(
		"Sample",
		filters={"test_request": test_request},
		fields=["name", "sample_name", "received_date", "status", "qty", "uom", "remarks"],
		order_by="sample_name asc",
	)


@frappe.whitelist()
def create_sample(data):
	require_roles(ALL_STAFF_ROLES)
	data = data or {}
	if not data.get("test_request"):
		frappe.throw("请选择检测请求")
	_require_editable_request(data["test_request"])
	doc = frappe.new_doc("Sample")
	doc.test_request = data["test_request"]
	doc.sample_name = data.get("sample_name")
	doc.received_date = data.get("received_date")
	doc.status = data.get("status") or "待收样"
	doc.qty = data.get("qty") or 1
	doc.uom = data.get("uom")
	doc.remarks = data.get("remarks")
	doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def update_sample(data):
	require_roles(ALL_STAFF_ROLES)
	data = data or {}
	doc = frappe.get_doc("Sample", data["name"])
	_require_editable_request(doc.test_request)
	for field in ("sample_name", "received_date", "status", "qty", "uom", "remarks"):
		if field in data:
			doc.set(field, data[field])
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def delete_sample(name):
	require_roles(ALL_STAFF_ROLES)
	doc = frappe.get_doc("Sample", name)
	_require_editable_request(doc.test_request)
	if frappe.db.exists(
		"Test Request Item",
		{"sample": name, "parent": doc.test_request},
	):
		frappe.throw("该样品已被测试项引用,不能删除")
	frappe.delete_doc("Sample", name)
	return {"name": name}
