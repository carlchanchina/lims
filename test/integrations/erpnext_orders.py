# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""ERPNext 报价单 / 销售订单 的查询与创建。

和 erpnext_masters.py 一样,LIMS 只做入口,单据都落在 ERPNext:
报价单由 Test Request 生成,销售订单由已提交的报价单转过来。
"""

import frappe
from frappe import _

QUOTATION_FIELDS = [
	"name",
	"party_name",
	"transaction_date",
	"grand_total",
	"currency",
	"status",
	"docstatus",
]

SALES_ORDER_FIELDS = [
	"name",
	"customer",
	"customer_name",
	"transaction_date",
	"grand_total",
	"currency",
	"status",
	"docstatus",
]


def _search(doctype, fields, txt=None, party_field=None, party=None, extra_filters=None):
	filters = dict(extra_filters or {})
	if party and party_field:
		filters[party_field] = party
	or_filters = None
	if txt:
		or_filters = [[doctype, "name", "like", f"%{txt}%"]]
		if party_field:
			or_filters.append([doctype, party_field, "like", f"%{txt}%"])
	return frappe.get_list(
		doctype,
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="modified desc",
		limit_page_length=30,
		ignore_permissions=True,
	)


def search_quotations(txt=None, customer=None):
	return _search("Quotation", QUOTATION_FIELDS, txt, "party_name", customer)


def search_sales_orders(txt=None, customer=None):
	return _search("Sales Order", SALES_ORDER_FIELDS, txt, "customer", customer)


def quotation_option(row):
	return {
		"name": row.name,
		"value": row.name,
		"label": _("{0} - {1} {2}").format(
			row.name, row.party_name or "", row.grand_total or 0
		).strip(),
	}


def sales_order_option(row):
	return {
		"name": row.name,
		"value": row.name,
		"label": _("{0} - {1} {2}").format(
			row.name, row.customer_name or row.customer or "", row.grand_total or 0
		).strip(),
	}


def sales_order_from_quotation(quotation_name, submit_quotation=True):
	"""把报价单转成 ERPNext 销售订单。

	ERPNext 的映射要求报价单已提交(docstatus=1),所以草稿报价单会先提交;
	新订单保持草稿状态,是否提交由业务在 ERPNext 决定。
	"""
	from erpnext.selling.doctype.quotation.quotation import make_sales_order

	quotation = frappe.get_doc("Quotation", quotation_name)
	if quotation.docstatus == 2:
		frappe.throw(_("报价单 {0} 已作废,不能转销售订单").format(quotation_name))
	if quotation.docstatus == 0:
		if not submit_quotation:
			frappe.throw(
				_("报价单 {0} 还是草稿,请先在 ERPNext 提交后再转销售订单").format(
					quotation_name
				)
			)
		quotation.flags.ignore_permissions = True
		quotation.submit()

	order = make_sales_order(quotation_name)
	order.flags.ignore_permissions = True
	order.insert(ignore_permissions=True)
	return order.name


def sales_order_items(sales_order):
	"""销售订单明细,用来生成委托请求的样品与测试项。"""
	doc = frappe.get_doc("Sales Order", sales_order)
	return [
		{
			"item_code": row.item_code,
			"item_name": row.item_name or row.item_code,
			"qty": row.qty,
			"uom": row.uom,
			"rate": row.rate,
			"amount": row.amount,
			"description": row.description,
		}
		for row in doc.items
	]
