# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def list_reports(filters=None, page=0, page_length=50):
	require_roles(ALL_STAFF_ROLES)
	filters = filters or {}
	return frappe.get_list(
		"Test Report",
		filters=filters,
		fields=[
			"name",
			"test_request",
			"sample",
			"sample_name",
			"report_date",
			"status",
			"customer",
			"item",
			"standard",
			"equipment",
			"tested_by",
			"conclusion",
			"remarks",
		],
		order_by="modified desc",
		start=int(page or 0),
		page_length=int(page_length or 50),
	)


@frappe.whitelist()
def get_report(name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc("Test Report", name).as_dict()


@frappe.whitelist()
def save_report(data):
	require_roles(ALL_STAFF_ROLES)
	data = data or {}
	name = data.get("name")
	doc = frappe.get_doc("Test Report", name) if name else frappe.new_doc("Test Report")
	fields = {
		"test_request",
		"sample",
		"report_date",
		"status",
		"item",
		"standard",
		"equipment",
		"tested_by",
		"conclusion",
		"remarks",
	}
	for field in fields & set(data):
		doc.set(field, data[field])
	if data.get("sample"):
		doc.sample_name = frappe.db.get_value(
			"Sample", data["sample"], "sample_name"
		)
	elif data.get("sample_name") is None:
		doc.sample_name = None
	if not name:
		doc.insert()
	else:
		doc.save()
	return {"name": doc.name}
