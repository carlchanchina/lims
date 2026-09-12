# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class TestReport(Document):
	def validate(self):
		if self.sample and self.test_request:
			request = frappe.db.get_value("Sample", self.sample, "test_request")
			if request and request != self.test_request:
				frappe.throw(
					_("样品 {0} 不属于检测请求 {1}").format(self.sample, self.test_request),
					title=_("样品不匹配"),
				)
		# 注意:提交(submit)时 Frappe 只跑 validate + before_submit,不跑 before_save,
		# 所以签发留痕必须放在 validate 里。
		self.stamp_sign_off()

	def stamp_sign_off(self):
		"""三级签发留痕:提交审核记检测人,审核通过记审核人,批准签发记批准人。

		状态由「检测报告签发」工作流驱动(见 lims/setup/quality_workflow.py),
		这里只负责把「谁在什么时候签的」记下来。
		"""
		user = frappe.session.user

		if self.status in ("待审核", "待批准", "已出具") and not self.tested_by:
			self.tested_by = user

		if self.status in ("待批准", "已出具"):
			if not self.reviewed_by:
				self.reviewed_by = user
			if not self.reviewed_on:
				self.reviewed_on = today()

		if self.status == "已出具":
			if not self.approved_by:
				self.approved_by = user
			if not self.approved_on:
				self.approved_on = today()
			if not self.issued_on:
				self.issued_on = self.approved_on
			if not self.report_date:
				self.report_date = today()

	def before_cancel(self):
		"""作废必须填原因,并记录作废人与日期;报告本身不删除,保留作废痕迹。"""
		if not (self.void_reason or "").strip():
			frappe.throw(_("请先填写作废原因,再作废报告"), title=_("缺少作废原因"))
		self.voided_by = frappe.session.user
		self.voided_on = today()


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
