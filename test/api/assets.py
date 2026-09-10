# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles

ASSET_FIELDS = [
	"name",
	"asset_name",
	"item_code",
	"asset_category",
	"status",
	"location",
	"custodian",
	"company",
]


@frappe.whitelist()
def list_assets(txt=None):
	"""ERPNext Asset 作为检测设备主数据。"""
	require_roles(ALL_STAFF_ROLES)
	or_filters = None
	if txt:
		or_filters = [
			["name", "like", f"%{txt}%"],
			["asset_name", "like", f"%{txt}%"],
			["item_code", "like", f"%{txt}%"],
			["location", "like", f"%{txt}%"],
		]
	return frappe.get_list(
		"Asset",
		or_filters=or_filters,
		fields=ASSET_FIELDS,
		order_by="asset_name asc",
		limit_page_length=50,
		ignore_permissions=True,
	)
