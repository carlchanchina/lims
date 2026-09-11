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
	if "tasks" in data:
		doc.set("tasks", [])
		for row in data["tasks"] or []:
			doc.append(
				"tasks",
				{
					"task_name": row.get("task_name"),
					"test_request_item": row.get("test_request_item"),
					"equipment": row.get("equipment"),
					"start_datetime": row.get("start_datetime"),
					"end_datetime": row.get("end_datetime"),
					"owner_user": row.get("owner_user"),
					"status": row.get("status") or "待执行",
					"remarks": row.get("remarks"),
				},
			)
	if name:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def generate_plan_from_request(test_request):
	"""按 Test Request 的测试项生成一份默认试验计划与设备任务。"""
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
	for row in request.get("items", []):
		plan.append(
			"tasks",
			{
				"task_name": row.item_name or row.item,
				"test_request_item": row.name,
				"equipment": row.equipment,
				"status": "待执行",
			},
		)
	plan.flags.ignore_permissions = True
	plan.insert(ignore_permissions=True)
	return {"name": plan.name}
