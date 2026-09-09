# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def get_summary():
	require_roles(ALL_STAFF_ROLES)
	rows = frappe.get_all("Test Request", fields=["status"])
	summary = {
		"草稿": 0,
		"已报价": 0,
		"待检测": 0,
		"检测中": 0,
		"已完成": 0,
		"已取消": 0,
	}
	for row in rows:
		summary[row.status] = summary.get(row.status, 0) + 1
	return summary


@frappe.whitelist()
def get_pending():
	require_roles(ALL_STAFF_ROLES)
	in_progress = frappe.get_all(
		"Test Request",
		filters={"status": "检测中"},
		fields=["name", "customer", "modified"],
		order_by="modified desc",
		limit_page_length=10,
	)
	pending_reports = []
	for doc in in_progress:
		if not frappe.db.exists("Test Report", {"test_request": doc.name}):
			pending_reports.append(doc)
	return {"in_progress": in_progress, "pending_reports": pending_reports}
