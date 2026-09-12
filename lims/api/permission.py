# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES


def has_app_permission():
	"""Desk 应用面板是否显示「旭博检测中心OS」入口。"""
	if frappe.session.user == "Guest":
		return False
	return bool(set(frappe.get_roles()) & ALL_STAFF_ROLES)
