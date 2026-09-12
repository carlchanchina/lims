# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

# 检测中心LIMSOS 的角色体系(见 lims/setup/install.py)。
# 主数据(标准/方法/协议价/行业)的管理者与 DocType 权限矩阵保持一致。
MANAGER_ROLES = {
	"System Manager",
	"总经理",
	"项目经理",
	"销售经理",
	"技术负责人",
	"质量负责人",
}
SALES_ROLES = {"总经理", "销售经理", "销售"}
LAB_ROLES = {"总经理", "项目经理", "检测工程师", "实验员", "技术负责人", "质量负责人"}
ALL_STAFF_ROLES = MANAGER_ROLES | SALES_ROLES | LAB_ROLES | {"客服", "AI管理员"}


def require_login():
	if frappe.session.user == "Guest":
		frappe.throw("请先登录", frappe.PermissionError)


def require_roles(roles=None):
	require_login()
	allowed = set(roles or ALL_STAFF_ROLES)
	if not allowed & set(frappe.get_roles()):
		frappe.throw("没有权限执行此操作", frappe.PermissionError)


def require_manager():
	require_roles(MANAGER_ROLES)
