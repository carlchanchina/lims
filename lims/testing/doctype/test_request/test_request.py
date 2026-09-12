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
		self.validate_required_by()
		self.sync_linked_statuses()

	def validate_required_by(self):
		if self.required_by and self.transaction_date and self.required_by < self.transaction_date:
			frappe.throw(_("要求完成日期不能早于委托日期"), title=_("日期不正确"))

	def sync_linked_statuses(self):
		"""报价/订单/报告各自的状态独立记录,避免和主状态互相打架。"""
		if self.quotation:
			self.quotation_status = (
				frappe.db.get_value("Quotation", self.quotation, "status")
				or self.quotation_status
			)
		else:
			self.quotation_status = None

		if self.sales_order:
			self.sales_order_status = (
				frappe.db.get_value("Sales Order", self.sales_order, "status")
				or self.sales_order_status
			)
		else:
			self.sales_order_status = None

		if not self.is_new():
			self.report_status = _report_status(self.name)

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


def _report_status(test_request):
	"""报告整体进度:没有报告 / 部分出具 / 已出具(全作废则算没有)。"""
	statuses = frappe.get_all(
		"Test Report", filters={"test_request": test_request}, pluck="status"
	)
	statuses = [status for status in statuses if status != "已作废"]
	if not statuses:
		return "未出报告"
	if all(status == "已出具" for status in statuses):
		return f"已出具({len(statuses)})"
	return f"部分出具({len(statuses)})"


def sync_request_report_status(doc, method=None, *args, **kwargs):
	"""报告新增/变更/删除后,刷新请求上的报告状态。"""
	_refresh_request_status(doc, "report_status", _report_status)


def sync_request_quotation_status(doc, method=None, *args, **kwargs):
	# 派生状态不推进 Test Request 的 modified,否则正在保存请求的调用方
	# 会碰到 TimestampMismatchError(例如报价→销售订单时回填 sales_order)。
	for name in frappe.get_all("Test Request", filters={"quotation": doc.name}, pluck="name"):
		frappe.db.set_value(
			"Test Request", name, "quotation_status", doc.status, update_modified=False
		)


def sync_request_sales_order_status(doc, method=None, *args, **kwargs):
	for name in frappe.get_all("Test Request", filters={"sales_order": doc.name}, pluck="name"):
		frappe.db.set_value(
			"Test Request", name, "sales_order_status", doc.status, update_modified=False
		)


def _refresh_request_status(doc, fieldname, compute):
	test_request = doc.get("test_request") if hasattr(doc, "get") else None
	if not test_request or not frappe.db.exists("Test Request", test_request):
		return
	frappe.db.set_value(
		"Test Request", test_request, fieldname, compute(test_request), update_modified=False
	)


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


def get_customer_industry(customer):
	"""客户所属行业,用来匹配行业协议价。

	客户是 ERPNext 的事实源,行业写在 Customer 的定制字段 lims_industry 上
	(LIMS Customer 镜像表已停用)。
	"""
	if not customer:
		return None
	if not frappe.db.has_column("Customer", "lims_industry"):
		return None
	return frappe.db.get_value("Customer", customer, "lims_industry")


def _get_agreement_price(item, customer):
	"""按 客户协议价 -> 行业协议价 -> 通用协议价 的顺序取价。

	三种范围在 Test Agreement Price 上互斥(客户/行业二选一,都留空即通用),所以
	只要按优先级取第一条命中的记录即可。
	"""
	rows = frappe.get_all(
		"Test Agreement Price",
		filters={"item": item, "enabled": 1},
		fields=["name", "catalog_name", "price", "uom", "tat_days", "customer", "industry"],
	)
	if not rows:
		frappe.throw(
			_("检测项目 {0} 还没有协议价,请先在「协议价」里配置").format(item),
			title=_("缺少协议价"),
		)

	industry = get_customer_industry(customer)
	match = None
	if customer:
		match = next((row for row in rows if row.customer == customer), None)
	if match is None and industry:
		match = next((row for row in rows if row.industry == industry), None)
	if match is None:
		match = next((row for row in rows if not row.customer and not row.industry), None)

	if match is None:
		frappe.throw(
			_("检测项目 {0} 没有适用于该客户的协议价(客户 {1} / 行业 {2} / 通用 都没有)").format(
				item, customer or "-", industry or "-"
			),
			title=_("缺少协议价"),
		)
	return frappe._dict(match)


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
	"""按协议价(Test Agreement Price)为 Test Request 生成 ERPNext Quotation。"""
	request = frappe.get_doc("Test Request", name)
	request.check_permission("write")

	if not request.get("items"):
		frappe.throw(_("请先添加测试项(样品 + 检测项目)"), title=_("缺少测试项"))

	if request.quotation:
		quotation_status = frappe.db.get_value(
			"Quotation", request.quotation, "docstatus"
		)
		if quotation_status is not None and cint(quotation_status) == 1:
			frappe.throw(
				_("报价单 {0} 已提交,如需重新报价请先在 ERPNext 作废原报价单").format(
					request.quotation
				),
				title=_("报价单已提交"),
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
		# 协议价仅作参考:配了按协议价带出,没配也不阻断,价格留 0 由业务在 ERPNext 手填。
		catalog = None
		try:
			catalog = _get_agreement_price(row.item, request.customer)
		except frappe.ValidationError:
			catalog = None
		rate = flt(catalog.price) if catalog else 0.0
		sample_name = frappe.db.get_value("Sample", row.sample, "sample_name") or ""

		item_details = frappe.db.get_value("Item", row.item, ["item_name", "stock_uom"])
		if not item_details:
			frappe.throw(
				_("检测项目 {0} 不存在,请检查测试项行").format(row.item),
				title=_("项目资料不完整"),
			)
		item_name, stock_uom = item_details

		description_lines = [
			(catalog.catalog_name if catalog else None)
			or row.item_name
			or item_name,
		]
		if row.standard:
			standard_code = (
				frappe.db.get_value("Test Standard", row.standard, "standard_code")
				or row.standard
			)
			description_lines.append(_("标准: {0}").format(standard_code))
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
				"rate": rate,
				"amount": flt(row.qty) * rate,
				"agreement_price": catalog.name if catalog else None,
				"equipment": row.equipment,
				"hours": row.hours,
				"cycles": row.cycles,
			},
		)

	if frappe.db.has_column("Quotation", "lims_test_request"):
		quotation.lims_test_request = request.name

	quotation.insert()

	frappe.db.set_value(
		"Test Request",
		request.name,
		{"status": STATUS_QUOTED, "quotation": quotation.name},
	)
	_record_quotation(request, quotation)

	return quotation.name


def _record_quotation(request, quotation):
	"""把每次生成的报价单记进报价历史,当前这张标 is_current。"""
	rows = [
		{
			"quotation": row.quotation,
			"quotation_date": row.quotation_date,
			"grand_total": row.grand_total,
			"status": row.status,
			"is_current": 0,
		}
		for row in request.get("quotations", [])
	]
	rows.append(
		{
			"quotation": quotation.name,
			"quotation_date": quotation.transaction_date,
			"grand_total": quotation.grand_total,
			"status": quotation.status,
			"is_current": 1,
		}
	)
	request.reload()
	request.set("quotations", rows)
	request.flags.ignore_permissions = True
	request.save(ignore_permissions=True)
