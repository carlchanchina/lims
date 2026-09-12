# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""客户门户 API(erpnext-nuxt 门户 BFF 专用)。

契约与 `erpnext-nuxt/nuxt-app/shared/types/portal.ts` 一一对应:
portal 侧只做转发与展示,字段拼装、状态翻译、数据隔离都在这里完成。

调用方身份(两种,都支持):

1. **门户集成账号**:带 `客户门户` 角色(通常是 API Key/Secret 用户),
   每次调用必须显式传 `customer`(门户自己知道当前登录的是哪家客户);
2. **客户联系人登录**:Website User 且挂在某个 Contact 上,
   客户由 session 反查得到,此时 `customer` 参数只能在其所属客户范围内。

任何情况下都不会把别的客户的数据返回出去。
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, strip_html
from frappe.utils.pdf import get_pdf

PORTAL_ROLE = "客户门户"
PRINT_FORMAT_REPORT = "检测报告"

# 我们的委托单状态 -> 门户状态
REQUEST_STATUS_MAP = {
	"草稿": "pending_sample",
	"已报价": "pending_sample",
	"待检测": "testing",
	"检测中": "testing",
	"已完成": "completed",
	"已取消": "closed",
}

# 状态 -> 门户进度百分比
REQUEST_PROGRESS = {
	"pending_sample": 10,
	"testing": 55,
	"review": 80,
	"completed": 100,
	"closed": 100,
}


# ---------------------------------------------------------------------------
# 身份与数据隔离
# ---------------------------------------------------------------------------


def _customers_of_user(user=None):
	"""查出这个登录用户能代表哪些客户(通过 Contact 的 Dynamic Link)。"""
	user = user or frappe.session.user
	contact = frappe.db.get_value("Contact", {"user": user}, "name")
	if not contact:
		contact = frappe.db.get_value("Contact Email", {"email_id": user}, "parent")
	if not contact:
		return []
	return frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "parent": contact, "link_doctype": "Customer"},
		pluck="link_name",
	)


def resolve_customer(customer=None):
	"""确定本次请求代表哪个客户,越权直接报错。"""
	if frappe.session.user == "Guest":
		frappe.throw(_("请先登录"), frappe.PermissionError)

	roles = set(frappe.get_roles())
	is_service = PORTAL_ROLE in roles or roles & {"System Manager", "总经理"}

	if is_service:
		if not customer:
			frappe.throw(_("缺少 customer 参数"), frappe.ValidationError)
		if not frappe.db.exists("Customer", customer):
			frappe.throw(_("客户 {0} 不存在").format(customer), frappe.DoesNotExistError)
		return customer

	allowed = _customers_of_user()
	if not allowed:
		frappe.throw(_("当前账号没有绑定任何客户,请联系业务人员"), frappe.PermissionError)
	if customer and customer not in allowed:
		frappe.throw(_("没有权限查看该客户的数据"), frappe.PermissionError)
	return customer or (allowed[0] if len(allowed) == 1 else allowed[0])


def _assert_belongs(doctype, name, customer, field="customer"):
	"""确认单据属于该客户,否则报错(防止换个单号越权查看)。"""
	if not frappe.db.exists(doctype, name):
		frappe.throw(_("{0} {1} 不存在").format(doctype, name), frappe.DoesNotExistError)
	owner = frappe.db.get_value(doctype, name, field)
	if owner != customer:
		frappe.throw(_("没有权限查看该单据"), frappe.PermissionError)
	return owner


def website_permission_for_customer_doc(doc, ptype="read", user=None, verbose=False):
	"""hooks.has_website_permission 的实现:客户联系人只能看自己公司的单据。

	挂在 Test Request / Test Report / Quotation 上,客户门户(以及打印视图)
	就能用 Frappe 原生权限体系访问自己的单据,而不是绕过权限。
	"""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	if user == "Guest":
		return False
	allowed = _customers_of_user(user)
	if not allowed:
		return False
	customer = doc.get("customer") or doc.get("party_name")
	return bool(customer and customer in allowed)


def _hd_customer(customer):
	"""Helpdesk 的工单挂的是 HD Customer,不是 ERPNext Customer,这里做映射(缺了就建)。"""
	if not frappe.db.exists("DocType", "HD Customer"):
		return None
	existing = frappe.db.get_value("HD Customer", {"erpnext_customer": customer}, "name")
	if existing:
		return existing

	source = frappe.get_doc("Customer", customer)
	doc = frappe.new_doc("HD Customer")
	doc.customer_name = source.customer_name
	doc.customer_type = source.customer_type or "Company"
	doc.erpnext_customer = source.name
	doc.email_id = source.get("email_id")
	doc.mobile_no = source.get("mobile_id") or source.get("mobile_no")

	# Helpdesk 用 HD Customer Member 子表判断"工单客户是否属于该联系人",
	# 所以建 HD Customer 时要把该客户下的联系人都挂上。
	contacts = _contacts_of_customer(customer)
	for contact in contacts:
		doc.append(
			"contacts",
			{
				"contact_name": contact.name,
				"is_manager": 1 if contact.get("is_primary_contact") else 0,
			},
		)
	if contacts:
		primary = next(
			(c for c in contacts if c.get("is_primary_contact")), contacts[0]
		)
		doc.primary_contact = primary.name
		doc.email_id = doc.email_id or primary.get("email_id")
		doc.mobile_no = doc.mobile_no or primary.get("mobile_no")
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


def _contacts_of_customer(customer):
	"""该客户下的联系人(通过 Contact 的 Dynamic Link 反查)。"""
	names = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "link_doctype": "Customer", "link_name": customer},
		pluck="parent",
	)
	if not names:
		return []
	return frappe.get_all(
		"Contact",
		filters={"name": ["in", names]},
		fields=["name", "full_name", "email_id", "mobile_no", "is_primary_contact"],
		order_by="is_primary_contact desc, name",
	)


# ---------------------------------------------------------------------------
# 字段拼装
# ---------------------------------------------------------------------------


def _customer_name(customer):
	if not customer:
		return ""
	return frappe.db.get_value("Customer", customer, "customer_name") or customer


def _request_portal_status(request):
	"""委托单对客户展示的状态:报告在审核阶段时显示 review。"""
	status = REQUEST_STATUS_MAP.get(request.status, "pending_sample")
	report_statuses = frappe.get_all(
		"Test Report",
		filters={"test_request": request.name, "docstatus": ["<", 2]},
		pluck="status",
	)
	if any(s in ("待审核", "待批准") for s in report_statuses):
		return "review"
	return status


def _request_summary(row):
	doc = frappe.get_doc("Test Request", row.name) if not isinstance(row, dict) else row
	status = _request_portal_status(doc)
	quotation = doc.get("quotation")
	report = frappe.db.get_value(
		"Test Report",
		{"test_request": doc.name, "docstatus": ["<", 2]},
		["name"],
		as_dict=True,
	)
	sample_name = frappe.db.get_value(
		"Sample", {"test_request": doc.name}, "sample_name"
	) or ""
	return {
		"id": doc.name,
		"number": doc.name,
		"title": sample_name or doc.name,
		"status": status,
		"progress": REQUEST_PROGRESS.get(status, 0),
		"customerName": _customer_name(doc.customer),
		"createdAt": str(doc.transaction_date or doc.creation),
		"expectedDate": str(doc.required_by or ""),
		"quotationNumber": quotation or None,
		"reportNumber": (report or {}).get("name"),
	}


def _request_detail(doc):
	samples = frappe.get_all(
		"Sample",
		filters={"test_request": doc.name},
		fields=["name", "sample_name", "client_sample_code", "qty", "uom", "status", "received_date"],
		order_by="sample_name",
	)
	lines = []
	for row in doc.items:
		lines.append(
			{
				"id": row.name,
				"catalogCode": row.item,
				"name": row.item_name or frappe.db.get_value("Item", row.item, "item_name") or row.item,
				"standard": frappe.db.get_value("Test Standard", row.standard, "standard_code")
				if row.standard
				else "",
				"unit": row.uom or "",
				"qty": flt(row.qty),
			}
		)

	report = frappe.db.get_value(
		"Test Report",
		{"test_request": doc.name, "docstatus": ["<", 2]},
		["name", "status"],
		as_dict=True,
	)

	timeline = [
		{
			"id": f"{doc.name}-created",
			"kind": "created",
			"title": "委托已受理",
			"description": f"委托单 {doc.name} 已创建",
			"time": str(doc.creation),
		}
	]
	if doc.get("quotation"):
		timeline.append(
			{
				"id": f"{doc.name}-quoted",
				"kind": "quoted",
				"title": "已出具报价",
				"description": doc.quotation,
				"time": str(doc.modified),
			}
		)
	for sample in samples:
		timeline.append(
			{
				"id": f"{sample.name}-received",
				"kind": "sample",
				"title": f"样品 {sample.sample_name} {'已收样' if sample.received_date else '待收样'}",
				"description": sample.status or "",
				"time": str(sample.received_date or sample.creation),
			}
		)
	if report:
		timeline.append(
			{
				"id": f"{report.name}-report",
				"kind": "report",
				"title": f"检测报告 {report.name}",
				"description": report.status,
				"time": str(doc.modified),
			}
		)

	detail = _request_summary(doc)
	detail.update(
		{
			"sampleName": samples[0].sample_name if samples else "",
			"reportId": report.name if report else None,
			"samples": [
				{
					"id": s.name,
					"code": s.client_sample_code or s.name,
					"name": s.sample_name,
					"qty": flt(s.qty),
					"unit": s.uom or "",
					"status": "received" if s.received_date else "pending",
					"receivedAt": str(s.received_date) if s.received_date else None,
				}
				for s in samples
			],
			"lines": lines,
			"timeline": timeline,
			"remark": strip_html(doc.remarks or ""),
		}
	)
	return detail


def _quotation_portal_status(doc):
	if doc.docstatus == 2:
		return "rejected"
	ack = doc.get("lims_customer_ack") if doc.meta.has_field("lims_customer_ack") else None
	if ack == "已接受":
		return "accepted"
	if ack == "已拒绝":
		return "rejected"
	if doc.status in ("Ordered", "Converted", "Partially Ordered") or doc.get("lims_test_request"):
		# 已经转成销售订单/项目,对客户就是"已接受"
		if doc.status in ("Ordered", "Converted", "Partially Ordered"):
			return "accepted"
	if doc.valid_till and getdate(doc.valid_till) < getdate(nowdate()):
		return "expired"
	return "pending"


def _quotation_detail(doc):
	lines = []
	for row in doc.items:
		lines.append(
			{
				"catalogCode": row.item_code,
				"name": row.item_name or row.item_code,
				"standard": (row.description or "").splitlines()[1] if row.description and "\n" in row.description else "",
				"unit": row.uom or "",
				"qty": flt(row.qty),
				"unitPrice": flt(row.rate),
				"amount": flt(row.amount),
				"tatDays": 0,
			}
		)
	request_name = doc.get("lims_test_request")
	sample_name = ""
	if request_name and frappe.db.exists("Test Request", request_name):
		sample_name = frappe.db.get_value("Sample", {"test_request": request_name}, "sample_name") or ""
	return {
		"id": doc.name,
		"number": doc.name,
		"status": _quotation_portal_status(doc),
		"customerName": _customer_name(doc.party_name),
		"sampleName": sample_name,
		"sampleQty": flt(lines[0]["qty"]) if lines else 0,
		"contactName": frappe.db.get_value("Contact", doc.contact_person, "full_name")
		if doc.contact_person
		else "",
		"contactPhone": frappe.db.get_value("Contact", doc.contact_person, "mobile_no")
		if doc.contact_person
		else "",
		"remark": strip_html(doc.terms or ""),
		"createdAt": str(doc.transaction_date or doc.creation),
		"validUntil": str(doc.valid_till or ""),
		"tatDays": 0,
		"total": flt(doc.grand_total),
		"currency": doc.currency or "CNY",
		"lines": lines,
		"notes": _quotation_notes(doc),
		"attachments": [],
		"testRequestNumber": request_name,
		"testRequestId": request_name,
		"customerAck": doc.get("lims_customer_ack") if doc.meta.has_field("lims_customer_ack") else None,
	}


def _quotation_notes(doc):
	"""客户与实验室在报价单上的往来留言(Frappe Comment)。"""
	notes = []
	for comment in frappe.get_all(
		"Comment",
		filters={"reference_doctype": "Quotation", "reference_name": doc.name, "comment_type": "Comment"},
		fields=["name", "content", "creation", "owner"],
		order_by="creation asc",
		limit_page_length=100,
	):
		sender = "customer" if comment.owner in _portal_users() else "lab"
		notes.append(
			{
				"id": comment.name,
				"sender": sender,
				"content": strip_html(comment.content or ""),
				"createdAt": str(comment.creation),
			}
		)
	return notes


def _portal_users():
	"""所有客户联系人/门户账号(用来判断留言是谁发的)。"""
	return {
		row.parent
		for row in frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": ["in", ["Customer", "客户门户"]]},
			fields=["parent"],
			limit_page_length=0,
		)
	}


def _report_detail(doc):
	rows = []
	for row in doc.items:
		item_name = frappe.db.get_value("Item", row.item, "item_name") or row.item
		rows.append(
			{
				"id": row.name,
				"itemName": item_name,
				"standard": frappe.db.get_value("Test Standard", row.standard, "standard_code")
				if row.standard
				else "",
				"samplePart": frappe.db.get_value("Sample", row.sample, "sample_name") or "",
				"unit": "",
				"result": row.result or "",
				"conclusion": row.verdict or "",
			}
		)
	sample_qty = 0
	if doc.sample:
		sample_qty = flt(frappe.db.get_value("Sample", doc.sample, "qty"))
	return {
		"id": doc.name,
		"number": doc.name,
		"testRequestNumber": doc.test_request or "",
		"title": f"{frappe.db.get_value('Sample', doc.sample, 'sample_name') or ''} 检测报告".strip(),
		"status": "issued" if doc.status == "已出具" else "draft",
		"customerName": _customer_name(doc.customer),
		"sampleName": frappe.db.get_value("Sample", doc.sample, "sample_name") or "",
		"sampleQty": sample_qty,
		"createdAt": str(doc.report_date or doc.creation),
		"issuedAt": str(doc.issued_on) if doc.issued_on and doc.status == "已出具" else None,
		"rows": rows,
		"downloadUrl": f"/api/method/lims.api.portal.download_report_pdf?name={doc.name}",
	}


def _ticket_status(doc):
	if doc.status == "Closed":
		return "closed"
	if doc.status in ("Resolved",):
		return "resolved"
	return "open"


def _ticket_detail(doc):
	messages = []
	for comment in frappe.get_all(
		"HD Ticket Comment",
		filters={"reference_ticket": doc.name},
		fields=["name", "content", "creation", "commented_by", "is_pinned"],
		order_by="creation asc",
	):
		sender = "customer" if "customer" in (comment.commented_by or "").lower() else "agent"
		messages.append(
			{
				"id": comment.name,
				"sender": sender,
				"content": strip_html(comment.content or ""),
				"createdAt": str(comment.creation),
				"attachments": [],
			}
		)
	request_name = doc.get("lims_test_request") if doc.meta.has_field("lims_test_request") else None
	return {
		"id": doc.name,
		"number": doc.name,
		"subject": doc.subject,
		"category": "other",
		"status": _ticket_status(doc),
		"createdAt": str(doc.creation),
		"updatedAt": str(doc.modified),
		"testRequestNumber": request_name,
		"messages": messages,
	}


# ---------------------------------------------------------------------------
# 门户接口
# ---------------------------------------------------------------------------


@frappe.whitelist()
def dashboard(customer=None):
	"""门户首页:统计 + 最近单据。"""
	customer = resolve_customer(customer)

	requests = frappe.get_all(
		"Test Request",
		filters={"customer": customer},
		fields=["name"],
		order_by="modified desc",
		limit_page_length=0,
	)
	request_names = [r.name for r in requests]

	pending_quotations = frappe.db.count(
		"Quotation", {"party_name": customer, "docstatus": 0}
	)
	in_progress = frappe.db.count(
		"Test Request", {"customer": customer, "status": ["in", ["待检测", "检测中", "已报价"]]}
	)
	completed = frappe.db.count("Test Request", {"customer": customer, "status": "已完成"})
	hd_customer = _hd_customer(customer)
	open_tickets = (
		frappe.db.count("HD Ticket", {"customer": hd_customer, "status": ["in", ["Open", "Replied"]]})
		if hd_customer
		else 0
	)

	recent_requests = []
	for name in request_names[:5]:
		recent_requests.append(_request_summary(frappe.get_doc("Test Request", name)))

	recent_quotations = [
		_quotation_detail(frappe.get_doc("Quotation", row.name)) for row in frappe.get_all(
			"Quotation",
			filters={"party_name": customer},
			fields=["name"],
			order_by="modified desc",
			limit_page_length=5,
		)
	]
	recent_reports = [
		_report_detail(frappe.get_doc("Test Report", row.name)) for row in frappe.get_all(
			"Test Report",
			filters={"test_request": ["in", request_names or [""]], "docstatus": ["<", 2]},
			fields=["name"],
			order_by="modified desc",
			limit_page_length=5,
		)
	]
	recent_tickets = list_tickets(customer=customer)[:5] if frappe.db.exists("DocType", "HD Ticket") else []

	return {
		"stats": {
			"pendingQuotations": pending_quotations,
			"inProgressTestRequests": in_progress,
			"completedTestRequests": completed,
			"awaitingPaymentAmount": 0,
			"openTickets": open_tickets,
		},
		"recentQuotations": recent_quotations,
		"recentTestRequests": recent_requests,
		"recentReports": recent_reports,
		"recentTickets": recent_tickets,
	}


@frappe.whitelist()
def list_test_requests(customer=None, status=None, keyword=None, page=0, page_length=20):
	customer = resolve_customer(customer)
	filters = {"customer": customer}
	if keyword:
		filters["name"] = ["like", f"%{keyword}%"]
	rows = frappe.get_all(
		"Test Request",
		filters=filters,
		fields=["name"],
		order_by="modified desc",
		start=cint(page) * cint(page_length),
		page_length=cint(page_length),
	)
	out = []
	for row in rows:
		summary = _request_summary(frappe.get_doc("Test Request", row.name))
		if status and summary["status"] != status:
			continue
		out.append(summary)
	return out


@frappe.whitelist()
def get_test_request(name, customer=None):
	customer = resolve_customer(customer)
	_assert_belongs("Test Request", name, customer)
	return _request_detail(frappe.get_doc("Test Request", name))


@frappe.whitelist()
def list_quotations(customer=None, status=None, page=0, page_length=20):
	customer = resolve_customer(customer)
	rows = frappe.get_all(
		"Quotation",
		filters={"party_name": customer},
		fields=["name"],
		order_by="modified desc",
		start=cint(page) * cint(page_length),
		page_length=cint(page_length),
	)
	out = []
	for row in rows:
		detail = _quotation_detail(frappe.get_doc("Quotation", row.name))
		if status and detail["status"] != status:
			continue
		out.append(detail)
	return out


@frappe.whitelist()
def get_quotation(name, customer=None):
	customer = resolve_customer(customer)
	_assert_belongs("Quotation", name, customer, field="party_name")
	return _quotation_detail(frappe.get_doc("Quotation", name))


@frappe.whitelist()
def add_quotation_note(name, content=None, customer=None):
	"""客户在门户对报价单留言(落在 Quotation 的 Comment 上,员工在 Desk 也能看到)。"""
	customer = resolve_customer(customer)
	_assert_belongs("Quotation", name, customer, field="party_name")
	content = (content or "").strip()
	if not content:
		frappe.throw(_("留言内容不能为空"))
	doc = frappe.get_doc("Quotation", name)
	doc.add_comment("Comment", text=content)
	return _quotation_detail(doc)


@frappe.whitelist()
def acknowledge_quotation(name, action="accept", reason=None, customer=None):
	"""客户确认/拒绝报价:写回定制字段 lims_customer_ack,并留一条备注。"""
	customer = resolve_customer(customer)
	_assert_belongs("Quotation", name, customer, field="party_name")
	if not frappe.db.has_column("Quotation", "lims_customer_ack"):
		frappe.throw(_("请先执行 migrate,补齐客户确认字段"))

	status = {"accept": "已接受", "reject": "已拒绝"}.get(action)
	if not status:
		frappe.throw(_("不支持的确认动作: {0}").format(action))

	frappe.db.set_value("Quotation", name, "lims_customer_ack", status, update_modified=False)
	doc = frappe.get_doc("Quotation", name)
	note = f"客户在门户{'接受' if action == 'accept' else '拒绝'}了本报价"
	if reason:
		note += f",说明:{reason}"
	doc.add_comment("Comment", text=note)
	return _quotation_detail(doc)


@frappe.whitelist()
def list_reports(customer=None, page=0, page_length=20):
	customer = resolve_customer(customer)
	request_names = frappe.get_all("Test Request", filters={"customer": customer}, pluck="name")
	if not request_names:
		return []
	rows = frappe.get_all(
		"Test Report",
		filters={"test_request": ["in", request_names], "docstatus": ["<", 2]},
		fields=["name"],
		order_by="modified desc",
		start=cint(page) * cint(page_length),
		page_length=cint(page_length),
	)
	return [_report_detail(frappe.get_doc("Test Report", row.name)) for row in rows]


@frappe.whitelist()
def get_report(name, customer=None):
	customer = resolve_customer(customer)
	report = frappe.get_doc("Test Report", name)
	if not report.test_request:
		frappe.throw(_("报告没有关联委托单"), frappe.PermissionError)
	_assert_belongs("Test Request", report.test_request, customer)
	return _report_detail(report)


@frappe.whitelist()
def download_report_pdf(name, customer=None):
	"""下载正式检测报告 PDF(带 CNAS/批准人的打印格式)。"""
	customer = resolve_customer(customer)
	get_report(name, customer=customer)  # 复用越权校验

	report = frappe.get_doc("Test Report", name)
	# 归属已经校验过;打印视图内部还会再查一次 read/print 权限,
	# 这里对这张单子显式放行,避免给门户账号开放整张表的打印权限。
	report.flags.ignore_permissions = True
	html = frappe.get_print("Test Report", name, print_format=PRINT_FORMAT_REPORT, doc=report)
	# 静态资源拉不到时(离线/内网域名解析不了)不要让整张 PDF 失败,内容仍然可读。
	pdf = get_pdf(
		html,
		options={"load-error-handling": "ignore", "load-media-error-handling": "ignore"},
	)
	frappe.local.response.filename = f"{name}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


@frappe.whitelist()
def list_catalog(customer=None, keyword=None, category=None):
	"""可送检的服务清单:检测项目(Item)+ 该客户适用的协议价。"""
	from lims.testing.doctype.test_request.test_request import get_customer_industry

	customer = resolve_customer(customer)
	industry = get_customer_industry(customer)
	price_rows = frappe.get_all(
		"Test Agreement Price",
		filters={"enabled": 1},
		fields=["name", "item", "price", "uom", "tat_days", "catalog_name"],
	)
	price_by_item = {}
	for row in price_rows:
		scope_rank = (
			0
			if row.get("item") and frappe.db.get_value("Test Agreement Price", row.name, "customer") == customer
			else 1
			if industry and frappe.db.get_value("Test Agreement Price", row.name, "industry") == industry
			else 2
		)
		current = price_by_item.get(row.item)
		if current is None or scope_rank < current[0]:
			price_by_item[row.item] = (scope_rank, row)

	items = frappe.get_all(
		"Item",
		filters={"is_sales_item": 1, "disabled": 0},
		fields=["name", "item_name", "item_group", "description", "stock_uom", "disabled"],
		order_by="item_name",
		limit_page_length=200,
	)
	out = []
	for item in items:
		if keyword and keyword.lower() not in (f"{item.name} {item.item_name}").lower():
			continue
		if category and category != item.item_group:
			continue
		scoped = price_by_item.get(item.name)
		out.append(
			{
				"code": item.name,
				"category": item.item_group or "",
				"name": item.item_name or item.name,
				"standard": "",
				"equipment": "",
				"unit": item.stock_uom or "",
				"price": flt(scoped[1].price) if scoped else 0,
				"tatDays": cint(scoped[1].tat_days) if scoped else 0,
			}
		)
	return out


@frappe.whitelist()
def create_inquiry(payload=None):
	"""客户在线委托/询价:建一张草稿委托单(客户 + 样品 + 检测项目)。"""
	payload = frappe.parse_json(payload) if isinstance(payload, str) else (payload or {})
	customer = resolve_customer(payload.get("customer"))

	services = payload.get("services") or []
	if not services:
		frappe.throw(_("请至少选择一个检测项目"))

	request = frappe.new_doc("Test Request")
	request.customer = customer
	request.contact = payload.get("contact")
	request.transaction_date = nowdate()
	request.required_by = payload.get("expectedDate") or None
	request.entrustment_mode = payload.get("entrustmentMode") or "送检"
	request.customer_reference = payload.get("reference")
	request.remarks = payload.get("remark")
	request.status = "草稿"
	request.flags.ignore_permissions = True
	request.insert(ignore_permissions=True)

	sample_name = payload.get("sampleName") or "客户送检样品"
	sample = frappe.new_doc("Sample")
	sample.test_request = request.name
	sample.sample_name = sample_name
	sample.client_sample_code = payload.get("sampleCode")
	sample.specification = payload.get("specification")
	sample.qty = flt(payload.get("sampleQty") or 1)
	sample.uom = payload.get("sampleUnit") or "Nos"
	sample.status = "待收样"
	sample.flags.ignore_permissions = True
	sample.insert(ignore_permissions=True)

	for code in services:
		item = frappe.db.get_value("Item", code, ["item_name", "stock_uom"], as_dict=True)
		if not item:
			continue
		request.append(
			"items",
			{
				"sample": sample.name,
				"item": code,
				"item_name": item.item_name,
				"qty": 1,
				"uom": item.stock_uom,
			},
		)
	request.flags.ignore_permissions = True
	request.save(ignore_permissions=True)

	return {
		"testRequestNumber": request.name,
		"sampleNumber": sample.name,
		"status": _request_portal_status(request),
	}


@frappe.whitelist()
def list_tickets(customer=None, page=0, page_length=20):
	customer = resolve_customer(customer)
	if not frappe.db.exists("DocType", "HD Ticket"):
		return []
	hd_customer = _hd_customer(customer)
	if not hd_customer:
		return []
	rows = frappe.get_all(
		"HD Ticket",
		filters={"customer": hd_customer},
		fields=["name"],
		order_by="modified desc",
		start=cint(page) * cint(page_length),
		page_length=cint(page_length),
	)
	return [_ticket_detail(frappe.get_doc("HD Ticket", row.name)) for row in rows]


@frappe.whitelist()
def get_ticket(name, customer=None):
	customer = resolve_customer(customer)
	ticket = frappe.get_doc("HD Ticket", name)
	if ticket.customer != _hd_customer(customer):
		frappe.throw(_("没有权限查看该工单"), frappe.PermissionError)
	return _ticket_detail(ticket)


@frappe.whitelist()
def add_ticket_message(name, content=None, customer=None):
	"""客户在门户回帖(写进 HD Ticket Comment,客服在 Helpdesk/Desk 都能看到)。"""
	customer = resolve_customer(customer)
	ticket = frappe.get_doc("HD Ticket", name)
	if ticket.customer != _hd_customer(customer):
		frappe.throw(_("没有权限查看该工单"), frappe.PermissionError)
	content = (content or "").strip()
	if not content:
		frappe.throw(_("回复内容不能为空"))

	comment = frappe.new_doc("HD Ticket Comment")
	comment.reference_ticket = ticket.name
	comment.content = content
	comment.commented_by = frappe.session.user
	comment.flags.ignore_permissions = True
	comment.insert(ignore_permissions=True)

	if ticket.status in ("Resolved", "Closed"):
		frappe.db.set_value("HD Ticket", ticket.name, "status", "Replied", update_modified=False)
	ticket.reload()
	return _ticket_detail(ticket)


@frappe.whitelist()
def create_ticket(subject=None, content=None, customer=None, test_request=None, category=None):
	"""客户在门户提交工单(落到 Helpdesk 的 HD Ticket)。"""
	customer = resolve_customer(customer)
	if not subject:
		frappe.throw(_("请填写工单标题"))
	if not frappe.db.exists("DocType", "HD Ticket"):
		frappe.throw(_("未安装 Helpdesk,无法受理工单"))

	hd_customer = _hd_customer(customer)
	ticket = frappe.new_doc("HD Ticket")
	ticket.subject = subject
	ticket.description = content or subject
	ticket.customer = hd_customer
	ticket.status = "Open"
	ticket.priority = "Medium"

	# 工单必须挂在"客户名下的联系人"上,Helpdesk 会校验这层关系。
	contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
	if not contact:
		contacts = _contacts_of_customer(customer)
		contact = contacts[0].name if contacts else None
	if contact:
		ticket.contact = contact
		ticket.raised_by = (
			frappe.db.get_value("Contact", contact, "email_id") or frappe.session.user
		)
	else:
		ticket.raised_by = frappe.session.user

	if test_request and ticket.meta.has_field("lims_test_request"):
		ticket.lims_test_request = test_request
	ticket.via_customer_portal = 1
	ticket.flags.ignore_permissions = True
	ticket.insert(ignore_permissions=True)

	return _ticket_detail(ticket)
