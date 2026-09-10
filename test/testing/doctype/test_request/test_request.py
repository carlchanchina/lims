# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, today

STATUS_DRAFT = "草稿"
STATUS_QUOTED = "已报价"
STATUS_TO_TEST = "待检测"
STATUS_IN_PROGRESS = "检测中"
STATUS_COMPLETED = "已完成"
STATUS_CANCELLED = "已取消"


class TestRequest(Document):
	def before_validate(self):
		self.set_company_defaults()

	def validate(self):
		self.fill_missing_item_details()

	def set_company_defaults(self):
		if not self.company:
			self.company = get_default_company()

	def fill_missing_item_details(self):
		for row in self.get("items", []):
			item_details = frappe.db.get_value(
				"Item", row.item, ["item_name", "stock_uom"]
			)
			if not item_details:
				continue
			item_name, stock_uom = item_details
			if not row.item_name:
				row.item_name = item_name
			if not row.uom:
				row.uom = stock_uom


def get_default_company():
	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
	)
	if company:
		return company
	companies = frappe.db.get_all("Company", pluck="name", limit=1)
	return companies[0] if companies else None


def _get_selling_price_list(customer, currency):
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


def _get_default_catalog(item, standard):
	"""返回 item + standard 的默认启用 Test Catalog,并处理缺失/歧义。"""
	filters = {
		"item": item,
		"standard": standard,
		"enabled": 1,
		"is_default": 1,
	}
	catalogs = frappe.get_all(
		"Test Catalog",
		filters=filters,
		fields=["name", "catalog_name", "price", "uom", "equipment", "is_default"],
	)
	if not catalogs:
		matches = frappe.get_all(
			"Test Catalog",
			filters={"item": item, "standard": standard, "enabled": 1},
			pluck="name",
		)
		if not matches:
			frappe.throw(
				_("未找到检测项目 {0} + 标准 {1} 的报价目录,请先在 Test Catalog 中配置价格").format(
					item, standard
				),
				title=_("缺少报价目录"),
			)
		frappe.throw(
			_("检测项目 {0} + 标准 {1} 有启用目录但未设置默认项,请先在 Test Catalog 中勾选 is_default").format(
				item, standard
			),
			title=_("未设置默认报价目录"),
		)
	if len(catalogs) > 1:
		frappe.throw(
			_("检测项目 {0} + 标准 {1} 存在多个默认报价目录,请保留一个 is_default").format(
				item, standard
			),
			title=_("默认报价目录冲突"),
		)
	return frappe._dict(catalogs[0])


@frappe.whitelist()
def sample_query(doctype, txt, searchfield, start, page_len, filters):
	"""返回指定 Test Request 下的样品,供测试项子表选择。"""
	filters = frappe._dict(filters or {})
	if not filters.get("test_request"):
		return []

	conditions = ["test_request = %(test_request)s"]
	values = {
		"test_request": filters.get("test_request"),
		"start": start,
		"page_len": page_len,
	}
	if txt:
		conditions.append("sample_name LIKE %(txt)s")
		values["txt"] = f"%{txt}%"

	return frappe.db.sql(
		"""
		SELECT name, sample_name
		FROM `tabSample`
		WHERE {conditions}
		ORDER BY sample_name
		LIMIT %(start)s, %(page_len)s
	""".format(conditions=" AND ".join(conditions)),
		values,
	)


@frappe.whitelist()
def create_quotation(name):
	"""按 Test Catalog 价格为 Test Request 生成 ERPNext Quotation。"""
	request = frappe.get_doc("Test Request", name)
	request.check_permission("write")

	if not request.get("items"):
		frappe.throw(_("请先添加测试项(样品 + 检测项目 + 标准)"), title=_("缺少测试项"))

	if request.quotation:
		quotation_status = frappe.db.get_value(
			"Quotation", request.quotation, "docstatus"
		)
		if quotation_status is not None and cint(quotation_status) != 2:
			frappe.throw(
				_("该请求已生成报价单 {0},如需重新报价请先取消/删除原报价单").format(
					request.quotation
				),
				title=_("报价单已存在"),
			)

	company = request.company or get_default_company()
	if not company:
		frappe.throw(_("请先为检测请求选择公司"), title=_("缺少公司"))

	currency = frappe.db.get_value("Company", company, "default_currency")
	if not currency:
		frappe.throw(
			_("公司 {0} 未设置默认币种,无法生成报价单").format(company),
			title=_("缺少币种"),
		)

	price_list = _get_selling_price_list(request.customer, currency)
	price_list_currency = (
		frappe.db.get_value("Price List", price_list, "currency") or currency
	)

	quotation = frappe.new_doc("Quotation")
	quotation.naming_series = _get_naming_series("Quotation")
	quotation.quotation_to = "Customer"
	quotation.party_name = request.customer
	quotation.contact_person = request.contact
	quotation.transaction_date = request.transaction_date or today()
	quotation.company = company
	quotation.order_type = "Sales"
	quotation.status = "Draft"
	quotation.currency = currency
	quotation.conversion_rate = 1.0
	quotation.selling_price_list = price_list
	quotation.price_list_currency = price_list_currency
	quotation.plc_conversion_rate = _get_conversion_rate(
		price_list_currency, currency, request.transaction_date
	)

	for row in request.get("items"):
		catalog = _get_default_catalog(row.item, row.standard)
		standard_code = frappe.db.get_value("Test Standard", row.standard, "standard_code")
		sample_name = frappe.db.get_value("Sample", row.sample, "sample_name") or ""

		item_details = frappe.db.get_value("Item", row.item, ["item_name", "stock_uom"])
		if not item_details:
			frappe.throw(
				_("检测项目 {0} 不存在,请检查测试项行").format(row.item),
				title=_("项目资料不完整"),
			)
		item_name, stock_uom = item_details

		description_lines = [
			catalog.catalog_name or row.item_name or item_name,
			_("标准: {0}").format(standard_code or row.standard),
		]
		if sample_name:
			description_lines.append(_("样品: {0}").format(sample_name))

		quotation.append(
			"items",
			{
				"item_code": row.item,
				"item_name": row.item_name or item_name,
				"description": "\n".join(description_lines),
				"qty": flt(row.qty) or 1.0,
				"uom": row.uom or stock_uom,
				"stock_uom": stock_uom,
				"conversion_factor": 1.0,
				"rate": flt(catalog.price),
				"amount": flt(row.qty) * flt(catalog.price),
				"test_catalog": catalog.name,
				"equipment": row.equipment or catalog.equipment,
				"hours": row.hours,
				"cycles": row.cycles,
			},
		)

	quotation.insert()

	frappe.db.set_value(
		"Test Request",
		request.name,
		{"status": STATUS_QUOTED, "quotation": quotation.name},
	)

	return quotation.name
