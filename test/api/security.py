# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

MANAGER_ROLES = {"System Manager", "Testing Manager"}
ALL_STAFF_ROLES = {"System Manager", "Testing Manager", "Testing User"}


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
