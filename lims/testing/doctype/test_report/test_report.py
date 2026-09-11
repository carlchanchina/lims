# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TestReport(Document):
	def validate(self):
		if self.sample and self.test_request:
			request = frappe.db.get_value("Sample", self.sample, "test_request")
			if request and request != self.test_request:
				frappe.throw(
					_("样品 {0} 不属于检测请求 {1}").format(self.sample, self.test_request),
					title=_("样品不匹配"),
				)


@frappe.whitelist()
def request_sample_query(doctype, txt, searchfield, start, page_len, filters):
	"""只返回当前 Test Request 下的样品,便于报告选择。"""
	filters = frappe._dict(filters or {})
	if not filters.get("test_request"):
		return []

	conditions = ["test_request = %(test_request)s"]
	values = {
		"test_request": filters.get("test_request"),
		"start": start,
		"page_len": page_len,
	}
	if txt:
		conditions.append("sample_name LIKE %(txt)s")
		values["txt"] = f"%{txt}%"

	return frappe.db.sql(
		"""
		SELECT name, sample_name
		FROM `tabSample`
		WHERE {conditions}
		ORDER BY sample_name
		LIMIT %(start)s, %(page_len)s
	""".format(conditions=" AND ".join(conditions)),
		values,
	)
