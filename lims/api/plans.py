# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def list_plans(filters=None):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_list(
		"Test Plan",
		filters=filters or {},
		fields=["name", "test_request", "status", "project", "start_date", "end_date", "modified"],
		order_by="modified desc",
	)


@frappe.whitelist()
def get_plan(name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc("Test Plan", name).as_dict()


@frappe.whitelist()
def save_plan(data):
	require_roles(ALL_STAFF_ROLES)
	data = data or {}
	name = data.get("name")
	doc = frappe.get_doc("Test Plan", name) if name else frappe.new_doc("Test Plan")
	for field in ("test_request", "status", "project", "start_date", "end_date", "remarks"):
		if field in data:
			doc.set(field, data[field])
	if name:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def generate_plan_from_request(test_request):
	"""按 Test Request 生成一份默认试验计划(只建计划头)。

	执行任务不在这里建:委托单保存时 `lims.integrations.erpnext_projects`
	已经把每个测试项同步成 Project 下的 ERPNext Task,计划只负责排期与备注。
	"""
	require_roles(ALL_STAFF_ROLES)
	if not frappe.db.exists("Test Request", test_request):
		frappe.throw("检测请求不存在")

	existing = frappe.db.exists("Test Plan", {"test_request": test_request})
	if existing:
		return {"name": existing}

	request = frappe.get_doc("Test Request", test_request)
	plan = frappe.new_doc("Test Plan")
	plan.test_request = request.name
	plan.status = "草稿"
	plan.project = request.get("project")
	plan.flags.ignore_permissions = True
	plan.insert(ignore_permissions=True)
	return {"name": plan.name}
