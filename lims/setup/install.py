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

# 客户门户(erpnext-nuxt)集成账号用;不是 Desk 角色。
PORTAL_ROLE = "客户门户"

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
	# 客服中心用 Helpdesk 的 HD Ticket 体系(权限走 Agent / Agent Manager 角色),
	# 这里只保留售后单据的只读权限。
	"Warranty Claim": ("总经理", "销售", "客服"),
	# 财务中心(ERPNext 财务模块,只读)。总经理在这个中心只看不改。
	"Account": ("总经理",),
	"Journal Entry": ("总经理",),
	"GL Entry": ("总经理",),
	"Sales Invoice": ("总经理",),
	"Purchase Invoice": ("总经理",),
	"Supplier": ("总经理",),
	"Payment Entry": ("总经理",),
	"Bank Account": ("总经理",),
	"Bank Transaction": ("总经理",),
	"Bank Reconciliation Tool": ("总经理",),
	"Cost Center": ("总经理",),
	"Period Closing Voucher": ("总经理",),
	"Payment Terms Template": ("总经理",),
	"Tax Category": ("总经理",),
	"Accounts Settings": ("总经理",),
}

# 中国客户分类:挂在 All Customer Groups 下的叶子分组(ERPNext 原生客户分组树)。
CHINESE_CUSTOMER_GROUPS = (
	"军工集团",
	"国有企业",
	"民营企业",
	"外资企业",
	"高校与科研院所",
	"政府机构",
	"同业分包",
)

# Helpdesk 有自己的角色体系(Agent / Agent Manager),检测中心的角色映射过去。
HELPDESK_ROLE_MAP = {
	"客服": "Agent",
	"销售": "Agent",
	"销售经理": "Agent Manager",
	"总经理": "Agent Manager",
	# 客户门户的集成账号要能"代客户建单",Helpdesk 只允许 Agent 这么做。
	PORTAL_ROLE: "Agent",
}

# ERPNext 财务模块的角色体系:财务报表(Balance Sheet / P&L / 总账 ...)只授权给
# Accounts User / Accounts Manager / Auditor。总经理在财务中心只读,所以映射到
# 只读的 Auditor,而不是有写权限的 Accounts User。
ACCOUNTING_ROLE_MAP = {
	"总经理": "Auditor",
}


def after_install():
	"""Runs once after the app is installed on a site."""
	run_schema_cleanup()
	ensure_starter_masters()


def run_schema_cleanup():
	"""安装与每次 migrate 后执行,保证角色/字段状态与当前版本一致。"""
	create_roles()
	sync_custom_fields()
	ensure_customer_groups()
	ensure_china_territories()
	ensure_helpdesk_roles()
	ensure_accounting_roles()
	grant_erpnext_read_permissions()
	remove_legacy_quotation_link_field()

	from lims.setup.quality_workflow import setup_quality

	setup_quality()


def ensure_helpdesk_roles():
	"""装了 Helpdesk 时,把我们的角色映射成它的 Agent / Agent Manager。

	Helpdesk 的 HD Ticket 等 DocType 只认 Agent / Agent Manager,
	不映射的话客服中心点进去是空的。
	"""
	if "helpdesk" not in frappe.get_installed_apps():
		return
	_ensure_mapped_roles(HELPDESK_ROLE_MAP)


def ensure_accounting_roles():
	"""装了 ERPNext 财务模块时,把总经理映射成只读的 Auditor。

	ERPNext 的财务报表只授权给 Accounts User / Accounts Manager / Auditor,
	不映射的话财务中心里「财务报表」那一组卡片会被静默隐藏。
	"""
	if "erpnext" not in frappe.get_installed_apps():
		return
	_ensure_mapped_roles(ACCOUNTING_ROLE_MAP)


def _ensure_mapped_roles(role_map):
	"""给持有源角色的用户补上目标角色(目标角色不存在时跳过)。"""
	role_users = {}
	for row in frappe.get_all(
		"Has Role", filters={"parenttype": "User"}, fields=["parent", "role"], limit_page_length=0
	):
		role_users.setdefault(row.role, set()).add(row.parent)

	for source_role, target_role in role_map.items():
		if not frappe.db.exists("Role", target_role):
			continue
		target_users = role_users.get(target_role, set())
		for user in role_users.get(source_role, set()) - target_users:
			user_doc = frappe.get_doc("User", user)
			user_doc.add_roles(target_role)


def ensure_starter_masters():
	"""补初始主数据:常用检测标准 / 检测方法 / 检测项目(只补缺,不覆盖)。

	老站点可以调用 `lims.api.master.seed_starter_masters` 手工执行一次。
	"""
	if not frappe.db.exists("DocType", "Test Standard"):
		return {"standards": 0, "methods": 0, "items": 0}

	from lims.data.starter_masters import STARTER_METHODS, STARTER_STANDARDS, STARTER_TEST_ITEMS

	created = {"standards": 0, "methods": 0, "items": 0}
	standard_by_code = {}

	for row in STARTER_STANDARDS:
		name = frappe.db.get_value("Test Standard", {"standard_code": row["standard_code"]}, "name")
		if not name:
			doc = frappe.new_doc("Test Standard")
			doc.standard_code = row["standard_code"]
			doc.standard_name = row["standard_name"]
			doc.version = row.get("version")
			doc.organization = row.get("organization")
			doc.status = row.get("status") or "现行"
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)
			name = doc.name
			created["standards"] += 1
		standard_by_code[row["standard_code"]] = name

	for row in STARTER_METHODS:
		if frappe.db.exists("Test Method", row["method_code"]):
			continue
		doc = frappe.new_doc("Test Method")
		doc.method_code = row["method_code"]
		doc.method_name = row["method_name"]
		doc.standard = standard_by_code.get(row.get("standard_code"))
		doc.status = "现行"
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		created["methods"] += 1

	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "Products"
	for row in STARTER_TEST_ITEMS:
		if frappe.db.exists("Item", row["item_code"]):
			continue
		doc = frappe.new_doc("Item")
		doc.item_code = row["item_code"]
		doc.item_name = row["item_name"]
		doc.item_group = item_group
		doc.stock_uom = "Nos"
		doc.is_stock_item = 0
		doc.is_sales_item = 1
		doc.is_purchase_item = 0
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		created["items"] += 1

	return created


def ensure_customer_groups():
	"""初始化中国客户分类(幂等;已存在就跳过,不动用户自己加的分组)。"""
	parent = "All Customer Groups"
	if not frappe.db.exists("Customer Group", parent):
		return
	for name in CHINESE_CUSTOMER_GROUPS:
		if frappe.db.exists("Customer Group", name):
			continue
		doc = frappe.new_doc("Customer Group")
		doc.customer_group_name = name
		doc.parent_customer_group = parent
		doc.is_group = 0
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)


def ensure_china_territories():
	"""地区树:China 改成组节点,下挂中国省级行政区(幂等)。

	省级以下(地级市/区县)按需维护,数据源见 lims/data/china_regions.py。
	"""
	from lims.data.china_regions import CHINA_CITIES, CHINA_PROVINCES, CHINA_TERRITORY

	if not frappe.db.exists("Territory", CHINA_TERRITORY):
		frappe.get_doc(
			{"doctype": "Territory", "territory_name": CHINA_TERRITORY, "is_group": 1}
		).insert(ignore_permissions=True)
	elif not frappe.db.get_value("Territory", CHINA_TERRITORY, "is_group"):
		china = frappe.get_doc("Territory", CHINA_TERRITORY)
		china.is_group = 1
		china.flags.ignore_permissions = True
		china.save(ignore_permissions=True)

	def _ensure(name, parent):
		if frappe.db.exists("Territory", name):
			return
		frappe.get_doc(
			{"doctype": "Territory", "territory_name": name, "parent_territory": parent, "is_group": 0}
		).insert(ignore_permissions=True)

	for province in CHINA_PROVINCES:
		_ensure(province, CHINA_TERRITORY)
	for province, cities in CHINA_CITIES.items():
		for city in cities:
			_ensure(city, province)


def create_roles():
	"""Create app roles referenced by Doctype permissions."""
	for role in DETECTION_OS_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)

	# 客户门户集成账号:不是 Desk 角色
	if not frappe.db.exists("Role", PORTAL_ROLE):
		frappe.get_doc(
			{"doctype": "Role", "role_name": PORTAL_ROLE, "desk_access": 0}
		).insert(ignore_permissions=True)

	for role in LEGACY_ROLES:
		# 停用旧角色,已分配的用户由 lims.setup.detection_os 迁移到新角色。
		if frappe.db.exists("Role", role) and not frappe.db.get_value("Role", role, "disabled"):
			frappe.db.set_value("Role", role, "disabled", 1)


def sync_custom_fields():
	"""LIMS 需要写回 ERPNext 的试验属性。"""
	custom_fields = {
			# 客户是 ERPNext 的事实源,这里补中国企业常用的工商/开票/分类信息。
			"Customer": [
				{
					"fieldname": "lims_short_name",
					"label": "企业简称",
					"fieldtype": "Data",
					"insert_after": "customer_name",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_industry",
					"label": "行业(协议价用)",
					"fieldtype": "Link",
					"options": "Industry",
					"insert_after": "customer_group",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_enterprise_nature",
					"label": "企业性质",
					"fieldtype": "Select",
					"options": "军工集团\n国有企业\n民营企业\n外资企业\n高校与科研院所\n政府机构\n事业单位\n其他",
					"insert_after": "lims_industry",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_customer_tier",
					"label": "客户分级",
					"fieldtype": "Select",
					"options": "战略客户\n重点客户\n普通客户\n潜在客户",
					"default": "普通客户",
					"insert_after": "lims_enterprise_nature",
					"no_copy": 1,
				},
				{
					"description": "营业执照上的法定代表人",
					"fieldname": "lims_legal_representative",
					"label": "法定代表人",
					"fieldtype": "Data",
					"insert_after": "territory",
					"no_copy": 1,
				},
				{
					"description": "营业执照注册地址(与开票地址/收样地址可能不同)",
					"fieldname": "lims_registered_address",
					"label": "注册地址",
					"fieldtype": "Small Text",
					"insert_after": "lims_legal_representative",
					"no_copy": 1,
				},
				{
					"description": "开票资料:名称用客户名称、税号用下方 Tax ID,这里补电话/开户行/账号",
					"fieldname": "lims_invoice_phone",
					"label": "开票电话",
					"fieldtype": "Data",
					"insert_after": "tax_category",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_bank_name",
					"label": "开户银行",
					"fieldtype": "Data",
					"insert_after": "lims_invoice_phone",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_bank_account",
					"label": "银行账号",
					"fieldtype": "Data",
					"insert_after": "lims_bank_name",
					"no_copy": 1,
				},
			],
			# 联系人:中文姓名 + 微信/分机,并标明谁收报告、谁对账。
			"Contact": [
				{
					"fieldname": "lims_role",
					"label": "联系人角色",
					"fieldtype": "Select",
					"options": "商务\n技术\n财务\n收样\n管理层\n其他",
					"insert_after": "designation",
					"no_copy": 1,
				},
				{
					"description": "中国企业常用微信沟通,记录微信号便于对接",
					"fieldname": "lims_wechat",
					"label": "微信",
					"fieldtype": "Data",
					"insert_after": "mobile_no",
					"no_copy": 1,
				},
				{
					"description": "座机分机号(座机本身写在电话字段,如 010-88886666)",
					"fieldname": "lims_extension",
					"label": "分机号",
					"fieldtype": "Data",
					"insert_after": "phone",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_receives_report",
					"label": "接收检测报告",
					"fieldtype": "Check",
					"insert_after": "is_primary_contact",
					"no_copy": 1,
				},
				{
					"fieldname": "lims_receives_invoice",
					"label": "接收发票/对账",
					"fieldtype": "Check",
					"insert_after": "lims_receives_report",
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
				{
					"description": "客户在门户上确认报价后回写",
					"fieldname": "lims_customer_ack",
					"label": "客户确认",
					"fieldtype": "Select",
					"options": "待确认\n已接受\n已拒绝",
					"default": "待确认",
					"insert_after": "lims_test_request",
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
					# 「待校准设备」指标卡按这个字段过滤,数据量大后要索引。
					"search_index": 1,
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
	}

	# Helpdesk 的工单要能回链到委托单(装了 Helpdesk 才有 HD Ticket)。
	if frappe.db.exists("DocType", "HD Ticket"):
		custom_fields["HD Ticket"] = [
			{
				"fieldname": "lims_test_request",
				"label": "LIMS 委托请求",
				"fieldtype": "Link",
				"options": "Test Request",
				"insert_after": "subject",
				"no_copy": 1,
			},
		]

	create_custom_fields(custom_fields, ignore_validate=True)
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
