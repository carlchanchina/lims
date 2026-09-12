# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TestMethod(Document):
	def validate(self):
		if self.superseded_by and self.status != "作废":
			frappe.throw(_("只有「作废」的方法才能指定被替代为"), title=_("状态不正确"))
