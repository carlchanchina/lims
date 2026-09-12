# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission

DETECTION_OS_ROLES = (
	"总经理",
	"销售经理",
	"销售",
	"项目经理",
	"检测工程师",
	"实验员",
	"技术负责人",
	"质量负责人",
	"客服",
	"AI管理员",
)

# 旧版本的角色:保留记录但停用,避免历史 DocPerm / 用户角色引用直接断链。
LEGACY_ROLES = ("Testing Manager", "Testing User")

# 各组角色需要读取的 ERPNext 主数据 / 单据(只授予 read)。
ERPNext_READ_GRANTS = {
	"Customer": ("总经理", "销售经理", "销售", "项目经理", "检测工程师", "实验员", "客服"),
	"Contact": ("总经理", "销售经理", "销售", "项目经理", "检测工程师", "实验员", "客服"),
	"Item": ("总经理", "销售经理", "销售", "项目经理", "检测工程师", "实验员"),
	"Asset": ("总经理", "项目经理", "检测工程师", "实验员", "技术负责人"),
	"Location": ("总经理", "实验员", "技术负责人"),
	"Asset Maintenance": ("总经理", "实验员", "技术负责人"),
	"Asset Maintenance Log": ("总经理", "实验员", "技术负责人"),
	"Asset Repair": ("总经理", "实验员", "技术负责人"),
	"Quotation": ("总经理", "销售经理", "销售", "项目经理"),
	"Sales Order": ("总经理", "销售经理", "销售", "项目经理"),
	"Lead": ("总经理", "销售经理", "销售"),
	"Opportunity": ("总经理", "销售经理", "销售"),
	"Prospect": ("总经理", "销售经理", "销售"),
	"Contract": ("总经理", "销售经理", "销售"),
	"Project": ("总经理", "销售经理", "销售", "项目经理", "检测工程师"),
	"Task": ("总经理", "项目经理", "检测工程师", "实验员"),
	"Issue": ("总经理", "销售", "客服"),
	"Issue Type": ("总经理", "销售", "客服"),
	"Issue Priority": ("总经理", "销售", "客服"),
	"Service Level Agreement": ("总经理", "客服"),
	"Warranty Claim": ("总经理", "销售", "客服"),
}


def after_install():
	"""Runs once after the app is installed on a site."""
	run_schema_cleanup()
	backfill_parties()


def run_schema_cleanup():
	"""安装与每次 migrate 后执行,保证角色/字段状态与当前版本一致。"""
	create_roles()
	sync_custom_fields()
	grant_erpnext_read_permissions()
	remove_legacy_quotation_link_field()


def backfill_parties():
	from lims.integrations.erpnext_party import backfill_parties as _backfill

	_backfill()


def create_roles():
	"""Create app roles referenced by Doctype permissions."""
	for role in DETECTION_OS_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)

	for role in LEGACY_ROLES:
		# 停用旧角色,已分配的用户由 lims.setup.detection_os 迁移到新角色。
		if frappe.db.exists("Role", role) and not frappe.db.get_value("Role", role, "disabled"):
			frappe.db.set_value("Role", role, "disabled", 1)


def sync_custom_fields():
	"""LIMS 需要写回 ERPNext 的试验属性。"""
	create_custom_fields(
		{
			# LIMS 与 ERPNext 共用同一张表:客户行业/回链字段都加在 ERPNext DocType 上。
			"Customer": [
				{
					"fieldname": "lims_industry",
					"label": "LIMS 行业",
					"fieldtype": "Link",
					"options": "Industry",
					"insert_after": "customer_group",
					"no_copy": 1,
				},
			],
			"Quotation": [
				{
					"fieldname": "lims_test_request",
					"label": "LIMS 委托请求",
					"fieldtype": "Link",
					"options": "Test Request",
					"insert_after": "transaction_date",
					"read_only": 1,
					"no_copy": 1,
				},
			],
			"Sales Order": [
				{
					"fieldname": "lims_test_request",
					"label": "LIMS 委托请求",
					"fieldtype": "Link",
					"options": "Test Request",
					"insert_after": "transaction_date",
					"read_only": 1,
					"no_copy": 1,
				},
			],
			"Project": [
				{
					"fieldname": "lims_test_request",
					"label": "LIMS 委托请求",
					"fieldtype": "Link",
					"options": "Test Request",
					"insert_after": "project_name",
					"read_only": 1,
					"no_copy": 1,
				},
			],
			"Task": [
				{
					"fieldname": "lims_test_request_item",
					"label": "LIMS 测试项",
					"fieldtype": "Link",
					"options": "Test Request Item",
					"insert_after": "subject",
					"read_only": 1,
					"no_copy": 1,
				},
			],
			"Quotation Item": [
				{
					"fieldname": "agreement_price",
					"label": "协议价",
					"fieldtype": "Link",
					"options": "Test Agreement Price",
					"insert_after": "item_code",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "equipment",
					"label": "设备(Asset)",
					"fieldtype": "Link",
					"options": "Asset",
					"insert_after": "agreement_price",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "hours",
					"label": "试验时长(h)",
					"fieldtype": "Float",
					"insert_after": "equipment",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "cycles",
					"label": "循环次数",
					"fieldtype": "Float",
					"insert_after": "hours",
					"read_only": 1,
					"no_copy": 1,
				},
			],
			# 设备校准:没有这三项就没法校验证书有效期。
			"Asset": [
				{
					"fieldname": "calibration_status",
					"label": "校准状态",
					"fieldtype": "Select",
					"options": "未校准\n合格\n不合格\n停用",
					"default": "未校准",
					"insert_after": "status",
				},
				{
					"fieldname": "last_calibration_date",
					"label": "上次校准日期",
					"fieldtype": "Date",
					"insert_after": "calibration_status",
				},
				{
					"fieldname": "calibration_due_date",
					"label": "校准有效期至",
					"fieldtype": "Date",
					"insert_after": "last_calibration_date",
				},
				{
					"fieldname": "calibration_interval_days",
					"label": "校准周期(天)",
					"fieldtype": "Int",
					"insert_after": "calibration_due_date",
					"description": "默认校准周期,新建校准记录时带出到期日",
				},
				{
					"fieldname": "cnas_no",
					"label": "CNAS 编号",
					"fieldtype": "Data",
					"insert_after": "calibration_interval_days",
				},
				{
					"fieldname": "capability_scope",
					"label": "能力范围",
					"fieldtype": "Small Text",
					"insert_after": "cnas_no",
				},
				{
					"fieldname": "frequency_range",
					"label": "频率范围",
					"fieldtype": "Data",
					"insert_after": "capability_scope",
				},
				{
					"fieldname": "thrust",
					"label": "推力",
					"fieldtype": "Data",
					"insert_after": "frequency_range",
				},
			],
		},
		ignore_validate=True,
	)
	remove_legacy_quotation_item_field()


def remove_legacy_quotation_item_field():
	"""协议价改名后,清掉 Quotation Item 上遗留的 test_catalog 字段。"""
	field_name = frappe.db.exists(
		"Custom Field", {"dt": "Quotation Item", "fieldname": "test_catalog"}
	)
	if field_name:
		frappe.delete_doc("Custom Field", field_name, force=1)


def grant_erpnext_read_permissions():
	"""让 Testing 角色能读取 LIMS 依赖的 ERPNext 主数据。"""
	for doctype, roles in ERPNext_READ_GRANTS.items():
		if not frappe.db.exists("DocType", doctype):
			# 例如 CRM / Helpdesk 未安装时相关单据不存在,跳过即可。
			continue
		for role in roles:
			try:
				add_permission(doctype, role)
			except Exception:
				pass


def remove_legacy_quotation_link_field():
	"""清理早期版本加在 Quotation 上的回链字段。"""
	field_name = frappe.db.exists(
		"Custom Field",
		{"dt": "Quotation", "fieldname": "testing_entrustment"},
	)
	if field_name:
		frappe.delete_doc("Custom Field", field_name, force=1)
