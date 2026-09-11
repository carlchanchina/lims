# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles

REPORT_FIELDS = [
	"name",
	"test_request",
	"sample",
	"report_date",
	"status",
	"customer",
	"tested_by",
	"reviewed_by",
	"approved_by",
	"issued_on",
	"conclusion",
	"remarks",
	"modified",
]

ITEM_ROW_FIELDS = (
	"test_request_item",
	"item",
	"standard",
	"standard_clause",
	"sample",
	"requirement",
	"result",
	"verdict",
	"equipment",
	"tested_by",
	"tested_on",
	"remarks",
)

HEADER_FIELDS = (
	"test_request",
	"sample",
	"report_date",
	"status",
	"tested_by",
	"reviewed_by",
	"approved_by",
	"issued_on",
	"conclusion",
	"remarks",
)


def _as_dict(value):
	if isinstance(value, str):
		return frappe.parse_json(value) or {}
	return value or {}


@frappe.whitelist()
def list_reports(filters=None, page=0, page_length=50):
	require_roles(ALL_STAFF_ROLES)
	rows = frappe.get_list(
		"Test Report",
		filters=filters or {},
		fields=REPORT_FIELDS,
		order_by="modified desc",
		start=int(page or 0),
		page_length=int(page_length or 50),
	)
	for row in rows:
		row["item_count"] = frappe.db.count(
			"Test Report Item", {"parent": row.name}
		)
	return rows


@frappe.whitelist()
def get_report(name):
	require_roles(ALL_STAFF_ROLES)
	return frappe.get_doc("Test Report", name).as_dict()


@frappe.whitelist()
def save_report(data=None):
	require_roles(ALL_STAFF_ROLES)
	data = _as_dict(data)
	name = data.get("name")
	doc = frappe.get_doc("Test Report", name) if name else frappe.new_doc("Test Report")

	for field in HEADER_FIELDS:
		if field in data:
			doc.set(field, data[field])

	if doc.test_request:
		doc.customer = frappe.db.get_value("Test Request", doc.test_request, "customer")

	if "items" in data:
		doc.set("items", [])
		for row in data.get("items") or []:
			doc.append("items", {field: row.get(field) for field in ITEM_ROW_FIELDS})

	if name:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def delete_report(name):
	require_roles(ALL_STAFF_ROLES)
	frappe.delete_doc("Test Report", name)
	return {"name": name}


@frappe.whitelist()
def report_item_defaults(test_request, test_request_item=None):
	"""建报告项时带出项目/标准/样品/设备,少填几格。"""
	require_roles(ALL_STAFF_ROLES)
	defaults = {"verdict": "待判定"}
	if test_request_item:
		row = frappe.db.get_value(
			"Test Request Item",
			test_request_item,
			["item", "standard", "sample", "equipment"],
			as_dict=True,
		)
		if row:
			defaults.update(row)
	if not defaults.get("item") and test_request:
		defaults["test_request"] = test_request
	return defaults
