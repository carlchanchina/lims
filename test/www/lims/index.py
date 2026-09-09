# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	frappe.db.commit()

	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/lims"
		return

	context.csrf_token = frappe.sessions.get_csrf_token()
	context.boot_json = frappe.as_json(get_boot())
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw("仅限 developer mode 使用")
	return get_boot()


def get_boot():
	return {
		"site_name": frappe.local.site,
		"csrf_token": frappe.sessions.get_csrf_token(),
		"session_user": frappe.session.user,
		"roles": frappe.get_roles(),
		"date_format": frappe.get_system_settings("date_format") or "yyyy-mm-dd",
		"time_format": frappe.get_system_settings("time_format") or "HH:mm:ss",
		"default_route": "/lims/dashboard",
		"can_manage": bool(
			set(frappe.get_roles()) & {"System Manager", "Testing Manager"}
		),
	}
