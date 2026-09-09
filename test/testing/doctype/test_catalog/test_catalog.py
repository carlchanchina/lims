# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TestCatalog(Document):
	def validate(self):
		self.validate_single_default()

	def validate_single_default(self):
		if not self.is_default or not self.enabled:
			return
		duplicate = frappe.db.exists(
			"Test Catalog",
			{
				"item": self.item,
				"standard": self.standard,
				"enabled": 1,
				"is_default": 1,
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw(
				_("检测项目 {0} + 标准 {1} 已存在默认报价目录 {2}").format(
					self.item, self.standard, duplicate
				),
				title=_("默认报价目录冲突"),
			)
