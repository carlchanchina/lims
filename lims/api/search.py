# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_roles

SEARCH_TARGETS = [
	{
		"doctype": "Test Request",
		"fields": ["name", "customer", "status"],
		"search_fields": ["name", "customer", "sales_order", "quotation"],
		"route": "/lims/requests/{name}",
		"title_field": "name",
		"subtitle_fields": ["customer", "status"],
	},
	{
		"doctype": "Sample",
		"fields": ["name", "sample_name", "status", "test_request"],
		"search_fields": ["name", "sample_name"],
		"route": "/lims/requests/{test_request}",
		"title_field": "sample_name",
		"subtitle_fields": ["name", "status"],
	},
	{
		"doctype": "Test Report",
		"fields": ["name", "test_request", "sample", "status"],
		"search_fields": ["name", "test_request", "sample", "conclusion"],
		"route": "/lims/reports?report={name}",
		"title_field": "name",
		"subtitle_fields": ["test_request", "status"],
	},
	{
		"doctype": "Test Agreement Price",
		"fields": ["name", "catalog_code", "catalog_name", "price"],
		"search_fields": ["name", "catalog_code", "catalog_name"],
		"route": "/lims/catalog",
		"title_field": "catalog_name",
		"subtitle_fields": ["catalog_code", "price"],
	},
	{
		"doctype": "Test Standard",
		"fields": ["name", "standard_code", "standard_name"],
		"search_fields": ["name", "standard_code", "standard_name"],
		"route": "/lims/standards",
		"title_field": "standard_code",
		"subtitle_fields": ["standard_name"],
	},
	{
		"doctype": "Asset",
		"fields": ["name", "asset_name", "item_code", "location"],
		"search_fields": ["name", "asset_name", "item_code", "location"],
		"route": "/lims/assets",
		"title_field": "asset_name",
		"subtitle_fields": ["name", "location"],
	},
]


@frappe.whitelist()
def global_search(txt=None):
	"""跨 LIMS 单据/主数据的全局搜索,供顶部搜索框使用。"""
	require_roles(ALL_STAFF_ROLES)
	txt = (txt or "").strip()
	if len(txt) < 2:
		return []

	results = []
	for target in SEARCH_TARGETS:
		try:
			rows = frappe.get_list(
				target["doctype"],
				or_filters=[
					[field, "like", f"%{txt}%"] for field in target["search_fields"]
				],
				fields=target["fields"],
				limit_page_length=6,
			)
		except frappe.PermissionError:
			continue

		for row in rows:
			results.append(
				{
					"doctype": target["doctype"],
					"name": row.name,
					"title": row.get(target["title_field"]) or row.name,
					"subtitle": " · ".join(
						str(row.get(field))
						for field in target["subtitle_fields"]
						if row.get(field)
					),
					"route": target["route"].format(**row),
				}
			)

	return results[:30]
