# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Sample(Document):
	def validate(self):
		self.set_customer_from_request()
		if not self.disposal and self.test_request:
			request_disposal = frappe.db.get_value(
				"Test Request", self.test_request, "sample_disposal"
			)
			if request_disposal in ("退还", "留样", "销毁"):
				self.disposal = request_disposal

	def set_customer_from_request(self):
		"""样品客户跟着委托请求走,避免两边填成不一致。"""
		if not self.test_request:
			return
		customer = frappe.db.get_value("Test Request", self.test_request, "customer")
		if customer:
			self.customer = customer
