# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class LIMSSettings(Document):
	"""检测机构级配置:机构名称、CNAS/CMA 编号、报告声明、默认报价条款。

	打印格式(检测委托单/检测报价单/检测报告)会读取这里的内容做抬头与页脚。
	"""

	pass
