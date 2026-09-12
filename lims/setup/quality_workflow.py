# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""检测报告的三级签发工作流 + 默认打印格式 + 实验室信息(都幂等)。

状态机(状态字段就是 Test Report.status):

    待检测 --开始检测--> 检测中 --提交审核--> 待审核 --审核通过--> 待批准 --批准签发--> 已出具
                                    |              |
                                    +--退回修改----+--> 检测中
    已出具 --作废--> 已作废(doc_status=2,走 Frappe cancel,自带留痕)

「已出具」对应 doc_status=1、「已作废」对应 doc_status=2,
所以批准时自动提交、作废时自动取消,审计痕迹由 Frappe 的 Version / Workflow 注释保留。
"""

import frappe

WORKFLOW_NAME = "检测报告签发"
STATE_FIELD = "status"

# (状态, doc_status, 允许编辑的角色, 样式)
# 注意:Workflow Document State.allow_edit 是必填,每个状态都要给一个角色。
STATES = (
	("待检测", "0", "检测工程师", "Info"),
	("检测中", "0", "检测工程师", "Primary"),
	("待审核", "0", "技术负责人", "Warning"),
	("待批准", "0", "质量负责人", "Warning"),
	("已出具", "1", "质量负责人", "Success"),
	("已作废", "2", "质量负责人", "Danger"),
)

# (当前状态, 动作, 下一状态, 允许角色)
TRANSITIONS = (
	("待检测", "开始检测", "检测中", "检测工程师"),
	("待检测", "开始检测", "检测中", "项目经理"),
	("检测中", "提交审核", "待审核", "检测工程师"),
	("检测中", "提交审核", "待审核", "项目经理"),
	("待审核", "审核通过", "待批准", "技术负责人"),
	("待审核", "退回修改", "检测中", "技术负责人"),
	("待批准", "批准签发", "已出具", "质量负责人"),
	("待批准", "退回修改", "检测中", "质量负责人"),
	("已出具", "作废", "已作废", "质量负责人"),
	("已出具", "作废", "已作废", "总经理"),
)

# DocType -> 默认打印格式(打印时不用每次挑)
DEFAULT_PRINT_FORMATS = {
	"Test Request": "检测委托单",
	"Quotation": "检测报价单",
	"Test Report": "检测报告",
}

DEFAULT_DISCLAIMER = (
	"1. 本报告仅对来样负责;报告未经本机构书面同意不得部分复制。\n"
	"2. 报告无检测、审核、批准人签字无效;报告涂改无效。\n"
	"3. 委托方对报告有异议,请在收到报告之日起 15 日内提出。"
)


def setup_quality():
	"""migrate 时调用:工作流 + 默认打印格式 + 实验室信息。"""
	ensure_report_workflow()
	ensure_default_print_formats()
	ensure_lims_settings()


def ensure_report_workflow():
	if not frappe.db.exists("DocType", "Test Report"):
		return

	for state, _doc_status, _role, style in STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)

	for _state, action, _next_state, _role in TRANSITIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		workflow = frappe.get_doc("Workflow", WORKFLOW_NAME)
	else:
		workflow = frappe.new_doc("Workflow")
		workflow.workflow_name = WORKFLOW_NAME

	workflow.document_type = "Test Report"
	workflow.workflow_state_field = STATE_FIELD
	workflow.is_active = 1
	workflow.send_email_alert = 0
	workflow.override_status = 0
	workflow.set("states", [])
	for state, doc_status, allow_edit, _style in STATES:
		workflow.append(
			"states",
			{
				"state": state,
				"doc_status": doc_status,
				"allow_edit": allow_edit,
				"is_optional_state": 0,
			},
		)
	workflow.set("transitions", [])
	for state, action, next_state, role in TRANSITIONS:
		workflow.append(
			"transitions",
			{
				"state": state,
				"action": action,
				"next_state": next_state,
				"allowed": role,
				"allow_self_approval": 1,
			},
		)
	workflow.flags.ignore_permissions = True
	workflow.save(ignore_permissions=True)


def ensure_default_print_formats():
	for doctype, print_format in DEFAULT_PRINT_FORMATS.items():
		if not frappe.db.exists("Print Format", print_format):
			continue
		_set_property(doctype, "default_print_format", print_format)


def _set_property(doctype, fieldname, value):
	"""给标准 DocType 加/更新一个 Property Setter(幂等)。"""
	existing = frappe.db.exists(
		"Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": fieldname}
	)
	if existing:
		if frappe.db.get_value("Property Setter", existing, "value") != value:
			frappe.db.set_value("Property Setter", existing, "value", value)
		return
	frappe.get_doc(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocType",
			"doc_type": doctype,
			"field_name": fieldname,
			"property": fieldname,
			"property_type": "Data",
			"value": value,
		}
	).insert(ignore_permissions=True)


def ensure_lims_settings():
	"""检测机构信息:空的时候填一个默认声明,名称取默认公司。"""
	if not frappe.db.exists("DocType", "LIMS Settings"):
		return
	settings = frappe.get_doc("LIMS Settings")
	changed = False
	if not settings.report_disclaimer:
		settings.report_disclaimer = DEFAULT_DISCLAIMER
		changed = True
	if not settings.company:
		company = frappe.defaults.get_global_default("company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		if company:
			settings.company = company
			changed = True
	if not settings.lab_name:
		company_name = settings.company or frappe.db.get_value("Company", {}, "name")
		if company_name:
			settings.lab_name = frappe.db.get_value("Company", company_name, "company_name") or company_name
			changed = True
	if changed:
		settings.flags.ignore_permissions = True
		settings.save(ignore_permissions=True)
