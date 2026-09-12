"""生成旭博检测中心OS 的 Desk 结构(10 个中心 / 侧边栏 / 指标卡 / 图表)。

用法:python dev_tools/build_desk_structure.py

生成的 JSON 会直接落到 lims/testing/workspace 等目录并提交进仓库;
Frappe 每次 migrate 都会重新导入它们,所以「文件即事实源」。
脚本每次都会盖新的 modified 时间戳,否则 migrate 会跳过导入。
"""

import json
import os
from datetime import datetime

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lims")
# Frappe 只在文件里的 modified 比数据库里新时才重新导入工作区,
# 所以每次生成都要盖一个新的 modified 时间戳。
CREATED = "2026-09-12 00:00:00.000000"
TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def write(path, doc):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		fh.write(json.dumps(doc, indent="\t", sort_keys=True, ensure_ascii=False) + "\n")


def block_id(prefix, i):
	return f"{prefix}{i:04d}"


def header(text, i):
	return {
		"id": block_id("hd", i),
		"type": "header",
		"data": {"text": f'<span class="h4"><b>{text}</b></span>', "col": 12},
	}


def paragraph(text, i):
	return {"id": block_id("pg", i), "type": "paragraph", "data": {"text": text, "col": 12}}


def spacer(i):
	return {"id": block_id("sp", i), "type": "spacer", "data": {"col": 12}}


def shortcut_block(name, col, i):
	return {"id": block_id("sc", i), "type": "shortcut", "data": {"shortcut_name": name, "col": col}}


def number_card_block(name, col, i):
	return {
		"id": block_id("nc", i),
		"type": "number_card",
		"data": {"number_card_name": name, "col": col},
	}


def card_block(name, col, i):
	return {"id": block_id("cd", i), "type": "card", "data": {"card_name": name, "col": col}}


def chart_block(name, i):
	return {"id": block_id("ch", i), "type": "chart", "data": {"chart_name": name, "col": 12}}


# --------------------------------------------------------------------------------------
# 10 个业务中心
# --------------------------------------------------------------------------------------

ALL_STAFF = []  # 不设 roles = 所有登录用户可见

ROLE_GROUPS = {
	"客户中心": ["总经理", "销售经理", "销售", "项目经理", "客服"],
	"销售中心": ["总经理", "销售经理", "销售"],
	"检测中心": ["总经理", "项目经理", "检测工程师", "实验员", "质量负责人"],
	"实验室": ["总经理", "检测工程师", "实验员", "技术负责人"],
	"质量中心": ["总经理", "实验员", "技术负责人", "质量负责人"],
	"客服中心": ["总经理", "销售", "客服"],
	"财务中心": ["总经理"],
	"系统管理": ["System Manager"],
}


def link_entry(label, doctype, dependencies=""):
	return {
		"dependencies": dependencies,
		"hidden": 0,
		"is_query_report": 0,
		"label": label,
		"link_count": 0,
		"link_to": doctype,
		"link_type": "DocType",
		"onboard": 0,
		"type": "Link",
	}


def report_entry(label, report_name):
	"""财务报表链接(link_type=Report,ERPNext 的 Query Report)。"""
	return {
		"dependencies": "",
		"hidden": 0,
		"is_query_report": 1,
		"label": label,
		"link_count": 0,
		"link_to": report_name,
		"link_type": "Report",
		"onboard": 0,
		"type": "Link",
	}


def card_break(label):
	return {
		"hidden": 0,
		"is_query_report": 0,
		"label": label,
		"link_count": 0,
		"onboard": 0,
		"type": "Card Break",
	}


def link_card(label, *links):
	entries = [link if isinstance(link, dict) else link_entry(*link) for link in links]
	return [card_break(label), *entries]


def new_shortcut(label, doctype, icon="add"):
	return {
		"color": "",
		"doc_view": "New",
		"icon": icon,
		"label": label,
		"link_to": doctype,
		"type": "DocType",
		"url": "",
	}


def url_shortcut(label, url, icon):
	return {
		"color": "",
		"icon": icon,
		"label": label,
		"link_to": None,
		"type": "URL",
		"url": url,
	}


CENTERS = [
	{"name": "首页", "icon": "home", "sequence": 1.0},
	{"name": "客户中心", "icon": "customer", "sequence": 2.0},
	{"name": "销售中心", "icon": "sell", "sequence": 3.0},
	{"name": "检测中心", "icon": "quality", "sequence": 4.0},
	{"name": "实验室", "icon": "assets", "sequence": 5.0},
	{"name": "质量中心", "icon": "review", "sequence": 6.0},
	{"name": "客服中心", "icon": "support", "sequence": 7.0},
	{"name": "财务中心", "icon": "accounting", "sequence": 8.0},
	{"name": "AI中心", "icon": "integration", "sequence": 9.0},
	{"name": "系统管理", "icon": "setting", "sequence": 10.0},
]

HOME_CARDS = ["待报价委托", "检测中委托", "待出报告", "本月销售", "进行中项目", "本月报告"]

WORKSPACES = {
	"首页": {
		"shortcuts": [
			url_shortcut(c["name"], f"/desk/{c['name']}", c["icon"])
			for c in CENTERS
			if c["name"] != "首页"
		],
		"number_cards": HOME_CARDS,
		"content": [
			header("今日概览", 1),
			*[number_card_block(n, 3, 10 + i) for i, n in enumerate(HOME_CARDS)],
			spacer(20),
			header("业务中心", 2),
			*[
				shortcut_block(c["name"], 3, 30 + i)
				for i, c in enumerate([c for c in CENTERS if c["name"] != "首页"])
			],
		],
	},
	"客户中心": {
		"links": link_card(
			"客户与联系人",
			("客户", "Customer"),
			("联系人", "Contact"),
			("客户分组", "Customer Group"),
			("地区", "Territory"),
			("地址", "Address"),
		),
		"shortcuts": [
			new_shortcut("+新建客户", "Customer"),
			new_shortcut("+新建联系人", "Contact"),
		],
		"content": [
			header("客户与联系人", 1),
			shortcut_block("+新建客户", 3, 2),
			shortcut_block("+新建联系人", 3, 3),
			spacer(4),
			card_block("客户与联系人", 4, 5),
		],
	},
	"销售中心": {
		"links": [
			*link_card("商机", ("线索", "Lead"), ("商机", "Opportunity"), ("潜在客户", "Prospect")),
			*link_card(
				"成交",
				("报价单", "Quotation"),
				("销售订单", "Sales Order"),
				("合同", "Contract"),
			),
			*link_card("交付", ("项目", "Project")),
		],
		"shortcuts": [
			new_shortcut("+商机", "Opportunity"),
			new_shortcut("+报价", "Quotation"),
			new_shortcut("+合同", "Contract"),
		],
		"number_cards": ["待跟进商机", "待处理报价"],
		"charts": ["销售漏斗"],
		"content": [
			header("商机与成交", 1),
			shortcut_block("+商机", 3, 2),
			shortcut_block("+报价", 3, 3),
			shortcut_block("+合同", 3, 4),
			spacer(5),
			number_card_block("待跟进商机", 3, 6),
			number_card_block("待处理报价", 3, 7),
			chart_block("销售漏斗", 8),
			spacer(9),
			card_block("商机", 4, 10),
			card_block("成交", 4, 11),
			card_block("交付", 4, 12),
		],
	},
	"检测中心": {
		"links": [
			*link_card("委托与样品", ("检测委托", "Test Request"), ("样品", "Sample")),
			*link_card(
				"执行",
				("试验计划", "Test Plan"),
				("设备使用记录", "Equipment Usage"),
				("项目", "Project"),
				("试验任务", "Task"),
			),
			*link_card(
				"交付",
				("检测报告", "Test Report"),
				("不合格/异常", "Test Nonconformance"),
			),
		],
		"shortcuts": [
			new_shortcut("+检测委托", "Test Request"),
			new_shortcut("+样品登记", "Sample"),
			new_shortcut("+试验计划", "Test Plan"),
			new_shortcut("+检测报告", "Test Report"),
		],
		"number_cards": ["待受理委托", "检测中委托", "待审核报告", "已完成委托", "超期委托"],
		"content": [
			header("检测委托", 1),
			shortcut_block("+检测委托", 3, 2),
			shortcut_block("+样品登记", 3, 3),
			shortcut_block("+试验计划", 3, 4),
			shortcut_block("+检测报告", 3, 5),
			spacer(6),
			header("进度", 7),
			number_card_block("待受理委托", 3, 8),
			number_card_block("检测中委托", 3, 9),
			number_card_block("待审核报告", 3, 10),
			number_card_block("已完成委托", 3, 11),
			number_card_block("超期委托", 3, 12),
			spacer(13),
			card_block("委托与样品", 4, 14),
			card_block("执行", 4, 15),
			card_block("交付", 4, 16),
		],
	},
	"实验室": {
		"links": [
			*link_card("设备台账", ("设备", "Asset"), ("实验室/位置", "Location")),
			*link_card("校准", ("校准记录", "Calibration Record")),
			*link_card(
				"维护",
				("维护计划", "Asset Maintenance"),
				("维护记录", "Asset Maintenance Log"),
				("维修", "Asset Repair"),
			),
			*link_card("使用", ("设备使用记录", "Equipment Usage")),
		],
		"shortcuts": [
			new_shortcut("+设备", "Asset"),
			new_shortcut("+校准记录", "Calibration Record"),
		],
		"number_cards": ["待校准设备", "维修中设备", "停机设备"],
		"content": [
			header("设备台账与校准", 1),
			shortcut_block("+设备", 3, 2),
			shortcut_block("+校准记录", 3, 3),
			spacer(4),
			number_card_block("待校准设备", 3, 5),
			number_card_block("维修中设备", 3, 6),
			number_card_block("停机设备", 3, 7),
			spacer(8),
			card_block("设备台账", 4, 9),
			card_block("校准", 4, 10),
			card_block("维护", 4, 11),
			card_block("使用", 4, 12),
		],
	},
	"质量中心": {
		"links": [
			*link_card("标准与方法", ("检测标准", "Test Standard"), ("检测方法", "Test Method")),
			*link_card("受控文件", ("质量文件", "Quality Document")),
			*link_card(
				"质量记录",
				("不合格/异常", "Test Nonconformance"),
				("检测报告", "Test Report"),
			),
		],
		"shortcuts": [
			new_shortcut("+标准", "Test Standard"),
			new_shortcut("+方法", "Test Method"),
			new_shortcut("+受控文件", "Quality Document"),
		],
		"number_cards": ["标准总数", "受控文件数", "待复审文件"],
		"content": [
			header("标准与受控文件", 1),
			shortcut_block("+标准", 3, 2),
			shortcut_block("+方法", 3, 3),
			shortcut_block("+受控文件", 3, 4),
			spacer(5),
			number_card_block("标准总数", 3, 6),
			number_card_block("受控文件数", 3, 7),
			number_card_block("待复审文件", 3, 8),
			spacer(9),
			card_block("标准与方法", 4, 10),
			card_block("受控文件", 4, 11),
			card_block("质量记录", 4, 12),
		],
	},
	"客服中心": {
		"links": [
			*link_card(
				"工单",
				("工单", "HD Ticket"),
				("问题类型", "HD Ticket Type"),
				("优先级", "HD Ticket Priority"),
				("工单状态", "HD Ticket Status"),
			),
			*link_card(
				"客服团队与 SLA",
				("客服组", "HD Team"),
				("服务协议", "HD Service Level Agreement"),
				("服务日历", "HD Service Holiday List"),
			),
			*link_card("知识库", ("知识文章", "HD Article"), ("文章分类", "HD Article Category")),
			*link_card(
				"售后与客户",
				("保修索赔", "Warranty Claim"),
				("客户", "Customer"),
				("联系人", "Contact"),
			),
		],
		"shortcuts": [new_shortcut("+新建工单", "HD Ticket")],
		"number_cards": ["待处理工单", "超时工单"],
		"content": [
			header("客户服务", 1),
			shortcut_block("+新建工单", 3, 2),
			spacer(3),
			number_card_block("待处理工单", 3, 4),
			number_card_block("超时工单", 3, 5),
			spacer(6),
			card_block("工单", 4, 7),
			card_block("客服团队与 SLA", 4, 8),
			card_block("知识库", 4, 9),
			card_block("售后与客户", 4, 10),
		],
	},
	"财务中心": {
		"links": [
			*link_card(
				"凭证与总账",
				("会计科目", "Account"),
				("日记账分录", "Journal Entry"),
				("总账分录", "GL Entry"),
				("期间结算凭证", "Period Closing Voucher"),
			),
			*link_card(
				"应收",
				("销售发票", "Sales Invoice"),
				("收款单", "Payment Entry"),
				("客户", "Customer"),
			),
			*link_card(
				"应付",
				("采购发票", "Purchase Invoice"),
				("付款单", "Payment Entry"),
				("供应商", "Supplier"),
			),
			*link_card(
				"资金与银行",
				("银行账户", "Bank Account"),
				("银行交易", "Bank Transaction"),
				("银行对账工具", "Bank Reconciliation Tool"),
			),
			*link_card(
				"财务报表",
				report_entry("资产负债表", "Balance Sheet"),
				report_entry("利润表", "Profit and Loss Statement"),
				report_entry("试算平衡表", "Trial Balance"),
				report_entry("总账", "General Ledger"),
				report_entry("现金流量表", "Cash Flow"),
				report_entry("应付账款汇总", "Accounts Payable Summary"),
			),
			*link_card(
				"财务设置",
				("财务设置", "Accounts Settings"),
				("成本中心", "Cost Center"),
				("税种", "Tax Category"),
				("付款条件模板", "Payment Terms Template"),
			),
		],
		"number_cards": ["本月开票", "应收未收", "应付未付", "本月回款"],
		"content": [
			header("财务概览", 1),
			number_card_block("本月开票", 3, 2),
			number_card_block("应收未收", 3, 3),
			number_card_block("应付未付", 3, 4),
			number_card_block("本月回款", 3, 5),
			spacer(6),
			card_block("凭证与总账", 4, 7),
			card_block("应收", 4, 8),
			card_block("应付", 4, 9),
			card_block("资金与银行", 4, 10),
			card_block("财务报表", 4, 11),
			card_block("财务设置", 4, 12),
		],
	},
	"AI中心": {
		"content": [
			header("AI 中心(规划中)", 1),
			paragraph(
				"报价助手 / 标准助手 / 报告助手 / 实验室助手 / 销售助手 将在二期接入,"
				"知识源为质量中心的标准、方法与受控文件。",
				2,
			),
		],
	},
	"系统管理": {
		"links": [
			*link_card("用户与权限", ("用户", "User"), ("角色", "Role"), ("角色档案", "Role Profile")),
			*link_card(
				"系统设置",
				("系统设置", "System Settings"),
				("表单定制", "Customize Form"),
				("自定义字段", "Custom Field"),
				("工作流", "Workflow"),
				("邮件账户", "Email Account"),
				("错误日志", "Error Log"),
			),
		],
		"content": [
			header("系统管理", 1),
			card_block("用户与权限", 4, 2),
			card_block("系统设置", 4, 3),
		],
	},
}


def workspace_doc(center, cfg):
	number_cards = [{"label": n, "number_card_name": n} for n in cfg.get("number_cards", [])]
	charts = [{"chart_name": c, "label": c} for c in cfg.get("charts", [])]
	return {
		"app": "lims",
		"charts": charts,
		"content": json.dumps(cfg["content"], ensure_ascii=False),
		"creation": CREATED,
		"custom_blocks": [],
		"docstatus": 0,
		"doctype": "Workspace",
		"for_user": "",
		"hide_custom": 0,
		"icon": center["icon"],
		"idx": 0,
		"is_hidden": 0,
		"label": center["name"],
		"links": cfg.get("links", []),
		"modified": TS,
		"modified_by": "Administrator",
		"module": "Testing",
		"name": center["name"],
		"number_cards": number_cards,
		"owner": "Administrator",
		"parent_page": "",
		"public": 1,
		"quick_lists": [],
		"restrict_to_domain": "",
		"roles": [{"role": r} for r in ROLE_GROUPS.get(center["name"], ALL_STAFF)],
		"sequence_id": center["sequence"],
		"shortcuts": cfg.get("shortcuts", []),
		"title": center["name"],
		"type": "Workspace",
	}


def sidebar_doc(center):
	items = []
	for c in CENTERS:
		items.append(
			{
				"child": 0,
				"collapsible": 1,
				"icon": c["icon"],
				"indent": 0,
				"keep_closed": 0,
				"label": c["name"],
				"link_to": c["name"],
				"link_type": "Workspace",
				"show_arrow": 0,
				"type": "Link",
			}
		)
	return {
		"app": "lims",
		"creation": CREATED,
		"docstatus": 0,
		"doctype": "Workspace Sidebar",
		"header_icon": center["icon"],
		"idx": 0,
		"items": items,
		"modified": TS,
		"modified_by": "Administrator",
		"module": "Testing",
		"module_onboarding": None,
		"name": center["name"],
		"owner": "Administrator",
		"standard": 1,
		"title": center["name"],
	}


for center in CENTERS:
	cfg = WORKSPACES[center["name"]]
	write(f"{ROOT}/testing/workspace/{center['name']}/{center['name']}.json", workspace_doc(center, cfg))
	write(f"{ROOT}/workspace_sidebar/{center['name']}.json", sidebar_doc(center))

# --------------------------------------------------------------------------------------
# Number Cards / Dashboard Chart
# --------------------------------------------------------------------------------------

MY = "本月"


def filters(*rows):
	return json.dumps(rows, ensure_ascii=False)


NUMBER_CARDS = {
	"待报价委托": {
		"document_type": "Test Request",
		"function": "Count",
		"filters_json": filters(["Test Request", "status", "=", "草稿"]),
	},
	"检测中委托": {
		"document_type": "Test Request",
		"function": "Count",
		"filters_json": filters(["Test Request", "status", "=", "检测中"]),
	},
	"待出报告": {
		"document_type": "Test Report",
		"function": "Count",
		"filters_json": filters(["Test Report", "status", "in", ["待检测", "检测中"]]),
	},
	"本月销售": {
		"document_type": "Sales Order",
		"function": "Sum",
		"aggregate_function_based_on": "grand_total",
		"filters_json": filters(
			["Sales Order", "docstatus", "=", 1],
			["Sales Order", "transaction_date", "Timespan", "this month"],
		),
		"show_percentage_stats": 1,
	},
	"进行中项目": {
		"document_type": "Project",
		"function": "Count",
		"filters_json": filters(["Project", "status", "=", "Open"]),
	},
	"本月报告": {
		"document_type": "Test Report",
		"function": "Count",
		"filters_json": filters(
			["Test Report", "status", "=", "已出具"],
			["Test Report", "report_date", "Timespan", "this month"],
		),
		"show_percentage_stats": 1,
	},
	"待跟进商机": {
		"document_type": "Opportunity",
		"function": "Count",
		"filters_json": filters(["Opportunity", "status", "in", ["Open", "Replied"]]),
	},
	"待处理报价": {
		"document_type": "Quotation",
		"function": "Count",
		"filters_json": filters(["Quotation", "docstatus", "=", 0]),
	},
	"待受理委托": {
		"document_type": "Test Request",
		"function": "Count",
		"filters_json": filters(["Test Request", "status", "=", "草稿"]),
	},
	"已完成委托": {
		"document_type": "Test Request",
		"function": "Count",
		"filters_json": filters(["Test Request", "status", "=", "已完成"]),
	},
	"超期委托": {
		"document_type": "Test Request",
		"function": "Count",
		"filters_json": filters(
			["Test Request", "required_by", "is", "set"],
			["Test Request", "status", "not in", ["已完成", "已取消"]],
		),
		"dynamic_filters_json": filters(
			["Test Request", "required_by", "<", "frappe.datetime.nowdate()"]
		),
	},
	"待校准设备": {
		"document_type": "Asset",
		"function": "Count",
		"filters_json": filters(["Asset", "calibration_due_date", "is", "set"]),
		"dynamic_filters_json": filters(
			[
				"Asset",
				"calibration_due_date",
				"<=",
				"frappe.datetime.add_days(frappe.datetime.nowdate(), 30).slice(0, 10)",
			]
		),
	},
	"维修中设备": {
		"document_type": "Asset Repair",
		"function": "Count",
		"filters_json": filters(["Asset Repair", "repair_status", "=", "Pending"]),
	},
	"停机设备": {
		"document_type": "Asset",
		"function": "Count",
		"filters_json": filters(["Asset", "status", "=", "Out of Order"]),
	},
	"标准总数": {
		"document_type": "Test Standard",
		"function": "Count",
		"filters_json": filters(),
	},
	"受控文件数": {
		"document_type": "Quality Document",
		"function": "Count",
		"filters_json": filters(["Quality Document", "status", "=", "受控"]),
	},
	"待复审文件": {
		"document_type": "Quality Document",
		"function": "Count",
		"filters_json": filters(
			["Quality Document", "status", "=", "受控"],
			["Quality Document", "review_due_date", "is", "set"],
		),
		"dynamic_filters_json": filters(
			[
				"Quality Document",
				"review_due_date",
				"<=",
				"frappe.datetime.add_days(frappe.datetime.nowdate(), 30).slice(0, 10)",
			]
		),
	},
	"待处理工单": {
		"document_type": "HD Ticket",
		"function": "Count",
		"filters_json": filters(["HD Ticket", "status", "in", ["Open", "Replied"]]),
	},
	"超时工单": {
		"document_type": "HD Ticket",
		"function": "Count",
		"filters_json": filters(["HD Ticket", "agreement_status", "=", "Failed"]),
	},
	"本月开票": {
		"document_type": "Sales Invoice",
		"function": "Sum",
		"aggregate_function_based_on": "grand_total",
		"filters_json": filters(
			["Sales Invoice", "docstatus", "=", 1],
			["Sales Invoice", "posting_date", "Timespan", "this month"],
		),
		"show_percentage_stats": 1,
	},
	"应收未收": {
		"document_type": "Sales Invoice",
		"function": "Sum",
		"aggregate_function_based_on": "outstanding_amount",
		"filters_json": filters(
			["Sales Invoice", "docstatus", "=", 1],
			["Sales Invoice", "outstanding_amount", ">", 0],
		),
	},
	"应付未付": {
		"document_type": "Purchase Invoice",
		"function": "Sum",
		"aggregate_function_based_on": "outstanding_amount",
		"filters_json": filters(
			["Purchase Invoice", "docstatus", "=", 1],
			["Purchase Invoice", "outstanding_amount", ">", 0],
		),
	},
	"本月回款": {
		"document_type": "Payment Entry",
		"function": "Sum",
		"aggregate_function_based_on": "paid_amount",
		"filters_json": filters(
			["Payment Entry", "docstatus", "=", 1],
			["Payment Entry", "payment_type", "=", "Receive"],
			["Payment Entry", "posting_date", "Timespan", "this month"],
		),
		"show_percentage_stats": 1,
	},
}

for label, cfg in NUMBER_CARDS.items():
	doc = {
		"creation": CREATED,
		"docstatus": 0,
		"doctype": "Number Card",
		"idx": 0,
		"is_public": 1,
		"is_standard": 1,
		"label": label,
		"modified": TS,
		"modified_by": "Administrator",
		"module": "Testing",
		"name": label,
		"owner": "Administrator",
		"show_percentage_stats": 0,
		"stats_time_interval": "Monthly",
		"type": "Document Type",
	}
	doc.update(cfg)
	write(f"{ROOT}/testing/number_card/{label}/{label}.json", doc)

CHART = {
	"chart_name": "销售漏斗",
	"chart_type": "Group By",
	"creation": CREATED,
	"custom_options": '{"height": 300}',
	"docstatus": 0,
	"doctype": "Dashboard Chart",
	"document_type": "Opportunity",
	"filters_json": "[]",
	"group_by_based_on": "status",
	"group_by_type": "Count",
	"idx": 0,
	"is_public": 1,
	"is_standard": 1,
	"modified": TS,
	"modified_by": "Administrator",
	"module": "Testing",
	"name": "销售漏斗",
	"number_of_groups": 0,
	"owner": "Administrator",
	"timeseries": 0,
	"type": "Bar",
	"use_report_chart": 0,
	"y_axis": [],
}
write(f"{ROOT}/testing/dashboard_chart/销售漏斗/销售漏斗.json", CHART)

print("workspaces:", len(CENTERS))
print("sidebars:", len(CENTERS))
print("number cards:", len(NUMBER_CARDS))
print("charts:", 1)
