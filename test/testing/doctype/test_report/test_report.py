# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TestReport(Document):
	pass


@frappe.whitelist()
def entrustment_sample_query(doctype, txt, searchfield, start, page_len, filters):
	"""只返回当前检测委托单下的样品行,便于报告选择。"""
	filters = frappe._dict(filters or {})
	if not filters.get("entrustment"):
		return []

	conditions = ["parent = %(entrustment)s"]
	values = {
		"entrustment": filters.get("entrustment"),
		"start": start,
		"page_len": page_len,
	}
	if txt:
		conditions.append("sample_name LIKE %(txt)s")
		values["txt"] = f"%{txt}%"

	return frappe.db.sql(
		"""
		SELECT name, sample_name
		FROM `tabTesting Entrustment Sample`
		WHERE {conditions}
		ORDER BY sample_name
		LIMIT %(start)s, %(page_len)s
	""".format(conditions=" AND ".join(conditions)),
		values,
	)
