# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""委托请求的报价单 / 销售订单:可以选 ERPNext 里已有的,也可以新建。"""

import frappe
from frappe.utils import today

from lims.api.security import ALL_STAFF_ROLES, require_roles
from lims.integrations import erpnext_orders


def _as_dict(value):
	if isinstance(value, str):
		return frappe.parse_json(value) or {}
	return value or {}


@frappe.whitelist()
def list_quotations(txt=None, customer=None):
	"""报价列表:直接读 ERPNext Quotation(事实源),供侧边栏「报价」页。"""
	require_roles(ALL_STAFF_ROLES)
	out = []
	for row in erpnext_orders.search_quotations(txt, customer):
		out.append(
			{
				"name": row.name,
				"customer": row.party_name,
				"transaction_date": row.transaction_date,
				"grand_total": row.grand_total,
				"currency": row.currency,
				"status": row.status,
				"docstatus": row.docstatus,
				"lims_test_request": _lims_ref("Quotation", row.name),
			}
		)
	return out


@frappe.whitelist()
def list_sales_orders(txt=None, customer=None):
	"""订单列表:直接读 ERPNext Sales Order(事实源),供侧边栏「订单」页。"""
	require_roles(ALL_STAFF_ROLES)
	out = []
	for row in erpnext_orders.search_sales_orders(txt, customer):
		out.append(
			{
				"name": row.name,
				"customer": row.customer,
				"customer_name": row.customer_name,
				"transaction_date": row.transaction_date,
				"grand_total": row.grand_total,
				"currency": row.currency,
				"status": row.status,
				"docstatus": row.docstatus,
				"lims_test_request": _lims_ref("Sales Order", row.name),
			}
		)
	return out


def _lims_ref(doctype, name):
	"""定制字段未 migrate 前优雅降级,返回 None。"""
	if frappe.db.has_column(doctype, "lims_test_request"):
		return frappe.db.get_value(doctype, name, "lims_test_request")
	return None


@frappe.whitelist()
def search_quotations(txt=None, customer=None):
	require_roles(ALL_STAFF_ROLES)
	return [
		erpnext_orders.quotation_option(row)
		for row in erpnext_orders.search_quotations(txt, customer)
	]


@frappe.whitelist()
def search_sales_orders(txt=None, customer=None):
	require_roles(ALL_STAFF_ROLES)
	return [
		erpnext_orders.sales_order_option(row)
		for row in erpnext_orders.search_sales_orders(txt, customer)
	]


@frappe.whitelist()
def link_quotation(name, quotation):
	"""把 ERPNext 里已有的一张报价单挂到委托请求上。"""
	require_roles(ALL_STAFF_ROLES)
	request = frappe.get_doc("Test Request", name)
	details = frappe.db.get_value(
		"Quotation", quotation, ["party_name", "docstatus"], as_dict=True
	)
	if not details:
		frappe.throw(f"报价单 {quotation} 不存在")
	if details.docstatus == 2:
		frappe.throw(f"报价单 {quotation} 已作废,不能关联")
	if request.customer and details.party_name != request.customer:
		frappe.throw("报价单的客户与委托请求的客户不一致")

	request.quotation = quotation
	if request.status == "草稿":
		request.status = "已报价"
	request.save(ignore_permissions=True)
	return {"name": request.name, "quotation": quotation, "status": request.status}


@frappe.whitelist()
def link_sales_order(name, sales_order):
	"""把 ERPNext 里已有的一张销售订单挂到委托请求上。"""
	require_roles(ALL_STAFF_ROLES)
	request = frappe.get_doc("Test Request", name)
	details = frappe.db.get_value(
		"Sales Order", sales_order, ["customer", "docstatus"], as_dict=True
	)
	if not details:
		frappe.throw(f"销售订单 {sales_order} 不存在")
	if details.docstatus == 2:
		frappe.throw(f"销售订单 {sales_order} 已作废,不能关联")
	if request.customer and details.customer != request.customer:
		frappe.throw("销售订单的客户与委托请求的客户不一致")

	request.sales_order = sales_order
	request.save(ignore_permissions=True)
	return {"name": request.name, "sales_order": sales_order}


@frappe.whitelist()
def create_sales_order(name):
	"""从请求关联的报价单生成 ERPNext 销售订单,并回填到请求上。"""
	require_roles(ALL_STAFF_ROLES)
	request = frappe.get_doc("Test Request", name)
	if not request.quotation:
		frappe.throw("请先生成或关联报价单,再由报价单生成销售订单")
	if request.sales_order and frappe.db.exists("Sales Order", request.sales_order):
		frappe.throw(f"该请求已关联销售订单 {request.sales_order}")

	sales_order = erpnext_orders.sales_order_from_quotation(request.quotation)
	request.sales_order = sales_order
	request.save(ignore_permissions=True)
	return {"name": request.name, "sales_order": sales_order}


@frappe.whitelist()
def create_request_from_sales_order(data=None):
	"""从销售订单建委托请求:带出客户与明细(每个明细建一条样品 + 测试项)。"""
	require_roles(ALL_STAFF_ROLES)
	data = _as_dict(data)
	sales_order = data.get("sales_order")
	if not sales_order:
		frappe.throw("请选择销售订单")

	order = frappe.get_doc("Sales Order", sales_order)
	if order.docstatus == 2:
		frappe.throw(f"销售订单 {sales_order} 已作废")

	request = frappe.new_doc("Test Request")
	request.customer = order.customer
	request.transaction_date = data.get("transaction_date") or today()
	request.company = data.get("company") or order.company
	request.sales_order = order.name
	request.status = "草稿"
	request.insert(ignore_permissions=True)

	for row in erpnext_orders.sales_order_items(order.name):
		sample = frappe.get_doc(
			{
				"doctype": "Sample",
				"test_request": request.name,
				"sample_name": row["item_name"] or row["item_code"],
				"qty": row["qty"] or 1,
				"uom": row["uom"],
				"status": "待收样",
			}
		).insert(ignore_permissions=True)
		request.append(
			"items",
			{
				"sample": sample.name,
				"item": row["item_code"],
				"qty": row["qty"] or 1,
				"uom": row["uom"],
				"remarks": row["description"],
			},
		)
	request.save(ignore_permissions=True)
	return {"name": request.name, "customer": request.customer, "item_count": len(request.items)}
