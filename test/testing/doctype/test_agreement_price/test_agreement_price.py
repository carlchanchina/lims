# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TestAgreementPrice(Document):
	def validate(self):
		self.validate_scope()
		self.validate_unique_scope()

	def validate_scope(self):
		"""协议价要么针对一个客户,要么针对一个行业,要么是通用价。"""
		if self.customer and self.industry:
			frappe.throw(
				_("协议价只能针对一个客户或一个行业,不能同时指定"),
				title=_("协议价范围冲突"),
			)

	def validate_unique_scope(self):
		"""同一 item + 范围只允许一条启用的协议价。"""
		if not self.enabled:
			return
		duplicate = frappe.db.exists(
			"Test Agreement Price",
			{
				"item": self.item,
				"customer": self.customer or "",
				"industry": self.industry or "",
				"enabled": 1,
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw(
				_("检测项目 {0} 对 {1} 已有启用的协议价 {2}").format(
					self.item, self.customer or self.industry or _("通用"), duplicate
				),
				title=_("协议价重复"),
			)
