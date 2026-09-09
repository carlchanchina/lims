# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, today

STATUS_DRAFT = "草稿"
STATUS_TO_BE_QUOTED = "待报价"
STATUS_QUOTATION_CREATED = "已报价"
STATUS_QUOTATION_ACCEPTED = "报价已确认"
STATUS_IN_PROGRESS = "检测中"
STATUS_COMPLETED = "已完成"
STATUS_CANCELLED = "已取消"


class TestingEntrustment(Document):
	def before_validate(self):
		self.set_company_defaults()

	def validate(self):
		self.update_amounts()

	def before_submit(self):
		if not self.get("items"):
			frappe.throw(_("请先在「委托项目」中添加至少一行检测项目"), title=_("缺少委托项目"))
		if self.status == STATUS_DRAFT:
			self.status = STATUS_TO_BE_QUOTED

	def on_cancel(self):
		if self.quotation:
			quotation_status = frappe.db.get_value("Quotation", self.quotation, "docstatus")
			if quotation_status is not None and cint(quotation_status) != 2:
				frappe.throw(
					_("请先取消报价单 {0},再取消该检测委托单").format(self.quotation),
					title=_("存在有效报价单"),
				)
			if quotation_status is None:
				self.quotation = None
		self.status = STATUS_CANCELLED

	def set_company_defaults(self):
		if not self.company:
			self.company = get_default_company()
		if self.company and not self.currency:
			self.currency = frappe.db.get_value("Company", self.company, "default_currency")

	def update_amounts(self):
		"""计算子表金额与委托单预计金额。"""
		total = 0.0
		for item in self.get("items", []):
			item.amount = flt(item.qty) * flt(item.rate)
			total += item.amount
		self.estimated_amount = flt(total, self.precision("estimated_amount"))


def get_default_company():
	"""用户/全局默认公司,回退到系统中第一家公司。"""
	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
	)
	if company:
		return company
	companies = frappe.db.get_all("Company", pluck="name", limit=1)
	return companies[0] if companies else None


def _get_selling_price_list(customer, currency):
	"""按客户默认价目表 -> Selling Settings 默认价目表 -> 启用中的同币种销售价目表。"""
	if customer:
		price_list = frappe.db.get_value("Customer", customer, "default_price_list")
		if price_list:
			return price_list

	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	if price_list:
		return price_list

	price_list = frappe.db.get_value(
		"Price List",
		{"selling": 1, "enabled": 1, "currency": currency},
		"name",
	)
	if price_list:
		return price_list

	frappe.throw(
		_("找不到适用于币种 {0} 的销售价目表。请为客户设置默认价目表,或在 Selling Settings 中配置默认销售价目表。").format(
			currency
		),
		title=_("缺少价目表"),
	)


def _get_naming_series(doctype):
	series = frappe.get_meta(doctype).get_field("naming_series")
	if not series or not series.options:
		return None
	for option in series.options.splitlines():
		if option.strip():
			return option.strip()
	return None


def _get_conversion_rate(from_currency, to_currency, transaction_date=None):
	if from_currency == to_currency:
		return 1.0
	from frappe.utils import get_exchange_rate

	return flt(get_exchange_rate(from_currency, to_currency, transaction_date), 6) or 1.0


@frappe.whitelist()
def create_quotation(name):
	"""从已提交的检测委托单生成一张报价单(ERPNext 为事实源)。"""
	entrustment = frappe.get_doc("Testing Entrustment", name)
	entrustment.check_permission("write")

	if entrustment.docstatus != 1:
		frappe.throw(_("只有已提交的检测委托单才能创建报价单"), title=_("状态不允许"))

	if not entrustment.get("items"):
		frappe.throw(_("该检测委托单没有委托项目,无法创建报价单"), title=_("缺少委托项目"))

	if entrustment.quotation:
		quotation_status = frappe.db.get_value(
			"Quotation", entrustment.quotation, "docstatus"
		)
		if quotation_status is not None and cint(quotation_status) != 2:
			frappe.throw(
				_("该委托单已关联报价单 {0},请先取消/删除原报价单后再重新创建").format(
					entrustment.quotation
				),
				title=_("报价单已存在"),
			)

	company = entrustment.company or get_default_company()
	if not company:
		frappe.throw(_("请先为检测委托单选择公司"), title=_("缺少公司"))

	currency = entrustment.currency or frappe.db.get_value(
		"Company", company, "default_currency"
	)
	if not currency:
		frappe.throw(
			_("公司 {0} 未设置默认币种,无法生成报价单").format(company),
			title=_("缺少币种"),
		)

	price_list = _get_selling_price_list(entrustment.customer, currency)
	price_list_currency = frappe.db.get_value("Price List", price_list, "currency") or currency

	quotation = frappe.new_doc("Quotation")
	quotation.naming_series = _get_naming_series("Quotation")
	quotation.quotation_to = "Customer"
	quotation.party_name = entrustment.customer
	quotation.contact_person = entrustment.contact
	quotation.transaction_date = entrustment.transaction_date or today()
	quotation.company = company
	quotation.order_type = "Sales"
	quotation.status = "Draft"
	quotation.currency = currency
	quotation.conversion_rate = 1.0
	quotation.selling_price_list = price_list
	quotation.price_list_currency = price_list_currency
	quotation.plc_conversion_rate = _get_conversion_rate(
		price_list_currency, currency, entrustment.transaction_date
	)

	if quotation.meta.has_field("testing_entrustment"):
		quotation.set("testing_entrustment", entrustment.name)

	for row in entrustment.get("items"):
		item_details = frappe.db.get_value(
			"Item", row.item, ["item_name", "stock_uom", "description"]
		)
		if not item_details:
			frappe.throw(
				_("检测项目 {0} 不存在或已被删除").format(row.item),
				title=_("项目资料不完整"),
			)
		item_name, stock_uom, description = item_details
		if not stock_uom:
			frappe.throw(
				_("检测项目 {0} 缺少库存计量单位(stock_uom),请先在 Item 中维护").format(row.item),
				title=_("项目资料不完整"),
			)
		quotation.append(
			"items",
			{
				"item_code": row.item,
				"item_name": row.item_name or item_name,
				"description": row.remarks or description or item_name,
				"qty": flt(row.qty),
				"uom": stock_uom,
				"stock_uom": stock_uom,
				"conversion_factor": 1.0,
				"rate": flt(row.rate),
				"amount": flt(row.amount or flt(row.qty) * flt(row.rate)),
			},
		)

	quotation.insert()

	frappe.db.set_value(
		"Testing Entrustment",
		entrustment.name,
		{"status": STATUS_QUOTATION_CREATED, "quotation": quotation.name},
	)

	return quotation.name
