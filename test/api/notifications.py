# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def list_notifications():
	"""LIMS 工作提醒:待报价、检测中未出报告。"""
	require_roles(ALL_STAFF_ROLES)
	items = []

	draft_requests = frappe.get_all(
		"Test Request",
		filters={"status": "草稿"},
		fields=["name", "customer", "modified"],
		order_by="modified desc",
		limit_page_length=10,
	)
	for row in draft_requests:
		if not frappe.db.count("Test Request Item", {"parent": row.name}):
			continue
		items.append(
			{
				"id": f"quote:{row.name}",
				"title": f"{row.name} 尚未生成报价",
				"description": "检测请求已有测试项,可以生成 ERPNext 报价单",
				"route": f"/lims/requests/{row.name}",
				"creation": row.modified,
			}
		)

	in_progress = frappe.get_all(
		"Test Request",
		filters={"status": ["in", ["待检测", "检测中"]]},
		fields=["name", "customer", "modified"],
		order_by="modified desc",
		limit_page_length=20,
	)
	for row in in_progress:
		if frappe.db.exists("Test Report", {"test_request": row.name}):
			continue
		items.append(
			{
				"id": f"report:{row.name}",
				"title": f"{row.name} 尚未出报告",
				"description": "该检测请求还没有关联的检测报告",
				"route": f"/lims/requests/{row.name}",
				"creation": row.modified,
			}
		)

	return items[:20]
