# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""受控质量文件(质量手册 / 程序文件 / 作业指导书 / 记录模板 / 外来文件)。"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class QualityDocument(Document):
	def validate(self):
		self.validate_controlled()
		self.validate_duplicate_number()

	def validate_controlled(self):
		"""文件转为「受控」时必须留下批准人和批准日期,否则质量体系追不回版本。"""
		if self.status != "受控":
			return
		if not self.approved_by:
			frappe.throw(_("文件转为「受控」前必须填写批准人"), title=_("缺少批准人"))
		if not self.approval_date:
			self.approval_date = today()
		if not self.revision_date:
			self.revision_date = self.approval_date

	def validate_duplicate_number(self):
		if not self.doc_number:
			return
		duplicate = frappe.db.exists(
			"Quality Document",
			{
				"doc_number": self.doc_number,
				"version": self.version,
				"status": ["!=", "已作废"],
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw(
				_("文件 {0} 的版本 {1} 已存在({2})").format(self.doc_number, self.version, duplicate),
				title=_("文件重复"),
			)
