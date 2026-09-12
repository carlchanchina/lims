# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_roles
from lims.api.samples import list_by_request
from lims.testing.doctype.test_request.test_request import create_quotation

EDITABLE_STATUSES = ("草稿", "已报价")


@frappe.whitelist()
def list_requests(filters=None, page=0, page_length=50):
	require_roles(ALL_STAFF_ROLES)
	filters = filters or {}
	docs = frappe.get_all(
		"Test Request",
		filters=filters,
		fields=[
			"name",
			"customer",
			"contact",
			"transaction_date",
			"customer_reference",
			"required_by",
			"entrustment_mode",
			"sample_disposal",
			"company",
			"status",
			"quotation",
			"sales_order",
			"quotation_status",
			"sales_order_status",
			"report_status",
			"modified",
		],
		order_by="modified desc",
		start=int(page or 0),
		page_length=int(page_length or 50),
	)
	result = []
	for doc in docs:
		sample_count = frappe.db.count("Sample", {"test_request": doc.name})
		report_count = frappe.db.count("Test Report", {"test_request": doc.name})
		result.append(
			{
				**doc,
				"customer_name": frappe.db.get_value(
					"Customer", doc.customer, "customer_name"
				),
				"sample_count": sample_count,
				"report_count": report_count,
			}
		)
	return result


@frappe.whitelist()
def get_request(name):
	require_roles(ALL_STAFF_ROLES)
	doc = frappe.get_doc("Test Request", name)
	return {
		**doc.as_dict(),
		"customer_name": frappe.db.get_value(
			"Customer", doc.customer, "customer_name"
		),
		"samples": list_by_request(name),
		"report_count": frappe.db.count("Test Report", {"test_request": name}),
	}


@frappe.whitelist()
def save_request(data):
	require_roles(ALL_STAFF_ROLES)
	data = data or {}
	name = data.get("name")
	doc = frappe.get_doc("Test Request", name) if name else frappe.new_doc("Test Request")

	for field in (
		"customer",
		"invoice_customer",
		"report_customer",
		"contact",
		"transaction_date",
		"customer_reference",
		"required_by",
		"entrustment_mode",
		"sample_disposal",
		"remarks",
		"company",
		"sales_order",
	):
		if field in data:
			doc.set(field, data[field])

	if not name:
		doc.status = "草稿"
	elif doc.status not in EDITABLE_STATUSES:
		frappe.throw("当前状态不允许编辑请求")

	if "items" in data:
		if doc.status != "草稿":
			frappe.throw("只有草稿请求可以修改测试项,请先取消报价后编辑")
		doc.items = []
		for row in data["items"] or []:
			doc.append(
				"items",
				{
					"sample": row.get("sample"),
					"item": row.get("item"),
					"standard": row.get("standard"),
					"qty": row.get("qty") or 1,
					"uom": row.get("uom"),
					"equipment": row.get("equipment"),
					"hours": row.get("hours"),
					"cycles": row.get("cycles"),
					"subcontracted": row.get("subcontracted") or 0,
					"subcontractor": row.get("subcontractor"),
					"remarks": row.get("remarks"),
				},
			)

	if name:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def request_action(name, action):
	require_roles(ALL_STAFF_ROLES)
	doc = frappe.get_doc("Test Request", name)

	if action == "generate_quotation":
		quotation = create_quotation(name)
		return {"name": name, "status": "已报价", "quotation": quotation}

	if action == "mark_ready":
		_assert_status(doc, "已报价")
		if not doc.sales_order:
			frappe.throw("请先填写销售定单")
		frappe.db.set_value("Test Request", name, "status", "待检测")
	elif action == "start":
		_assert_status(doc, "待检测")
		frappe.db.set_value("Test Request", name, "status", "检测中")
	elif action == "complete":
		_assert_status(doc, "检测中")
		frappe.db.set_value("Test Request", name, "status", "已完成")
	elif action == "cancel":
		if doc.status not in ("草稿", "已报价"):
			frappe.throw("当前状态不允许直接取消")
		if doc.quotation:
			q_status = frappe.db.get_value("Quotation", doc.quotation, "docstatus")
			if q_status is not None and q_status != 2:
				frappe.throw("请先取消关联的 ERPNext 报价单")
		frappe.db.set_value("Test Request", name, "status", "已取消")
	else:
		frappe.throw("未知动作")

	doc.reload()
	return {"name": doc.name, "status": doc.status}


def _assert_status(doc, status):
	if doc.status != status:
		frappe.throw(f"当前状态 {doc.status} 不允许该操作")
