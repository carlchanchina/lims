# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today

STATUS_DRAFT = "草稿"
STATUS_TO_TEST = "待检测"
STATUS_IN_PROGRESS = "检测中"
STATUS_COMPLETED = "已完成"
STATUS_CANCELLED = "已取消"


class TestingEntrustment(Document):
	def before_validate(self):
		self.set_company_defaults()

	def validate(self):
		self.fill_missing_uom()

	def before_submit(self):
		if not self.get("items"):
			frappe.throw(
				_("请先从销售定单导入或添加试验/检测项目"), title=_("缺少试验项目")
			)
		if not self.get("samples"):
			frappe.throw(
				_("每张检测委托单至少需要一个样品信息,请在「样品信息」中添加一行"),
				title=_("缺少样品信息"),
			)
		if self.status == STATUS_DRAFT:
			self.status = STATUS_TO_TEST

	def on_cancel(self):
		self.status = STATUS_CANCELLED

	def set_company_defaults(self):
		if not self.company:
			if self.sales_order:
				self.company = frappe.db.get_value(
					"Sales Order", self.sales_order, "company"
				)
			if not self.company:
				self.company = get_default_company()

	def fill_missing_uom(self):
		"""从 Item 补全未填写的计量单位。"""
		for row in self.get("items", []):
			if not row.uom:
				row.uom = frappe.db.get_value("Item", row.item, "stock_uom")
			if not row.item_name:
				row.item_name = frappe.db.get_value("Item", row.item, "item_name")


def get_default_company():
	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
	)
	if company:
		return company
	companies = frappe.db.get_all("Company", pluck="name", limit=1)
	return companies[0] if companies else None


@frappe.whitelist()
def get_sales_order_items(sales_order):
	"""
	读取已提交销售定单的明细,用于新建检测委托单时带入试验/检测项目。

	Sales Order 本身保持原样,本 App 不做任何字段/流程改动。
	"""
	if not sales_order:
		frappe.throw(_("请先选择销售定单"), title=_("缺少定单"))

	sales_order_doc = frappe.get_doc("Sales Order", sales_order)
	if sales_order_doc.docstatus != 1:
		frappe.throw(
			_("销售定单 {0} 尚未提交,请先提交定单再生成检测委托单").format(sales_order),
			title=_("定单未提交"),
		)

	items = []
	for row in sales_order_doc.get("items", []):
		items.append(
			{
				"item": row.item_code,
				"item_name": row.item_name,
				"qty": flt(row.qty),
				"uom": row.uom or row.stock_uom,
				"testing_standard": "",
				"remarks": row.get("additional_notes") or "",
			}
		)

	return {
		"customer": sales_order_doc.customer,
		"contact": sales_order_doc.contact_person,
		"company": sales_order_doc.company,
		"transaction_date": today(),
		"items": items,
	}
