"""生成检测中心的三个打印格式(委托单 / 报价单 / 检测报告)。

用法:python dev_tools/build_print_formats.py

HTML/CSS 在这里维护(便于 diff),生成的 JSON 落到
`lims/testing/print_format/<名称>/<名称>.json`,由 Frappe 在 migrate 时导入。
改完记得让 modified 比库里新——脚本每次运行都会盖当前时间。
"""

import json
import os
from datetime import datetime

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lims")
CREATED = "2026-09-12 00:00:00.000000"
TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

CSS = """
.print-format { font-size: 12px; color: #1f272e; }
.print-format .doc-header { display: flex; justify-content: space-between; border-bottom: 2px solid #1f272e; padding-bottom: 6px; margin-bottom: 12px; }
.print-format .lab-name { font-size: 18px; font-weight: bold; }
.print-format .lab-meta { color: #525c66; line-height: 1.5; }
.print-format .doc-title { text-align: right; }
.print-format .doc-title h1 { font-size: 20px; margin: 0; letter-spacing: 4px; }
.print-format .doc-title .doc-no { color: #525c66; margin-top: 4px; }
.print-format table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
.print-format th, .print-format td { border: 1px solid #b8c0c8; padding: 4px 6px; vertical-align: top; }
.print-format th { background: #f4f6f8; font-weight: 600; text-align: left; }
.print-format .kv th { width: 16%; background: #f8f9fa; }
.print-format .kv td { width: 34%; }
.print-format .num { text-align: right; }
.print-format .center { text-align: center; }
.print-format h3 { font-size: 13px; margin: 12px 0 6px; }
.print-format .muted { color: #6b7480; }
.print-format .sign td { height: 46px; }
.print-format .footer { margin-top: 14px; padding-top: 6px; border-top: 1px solid #b8c0c8; color: #6b7480; font-size: 11px; line-height: 1.6; }
"""

HEADER = """
{% set lab = frappe.get_doc("LIMS Settings") %}
<div class="doc-header">
	<div class="lab">
		<div class="lab-name">{{ lab.lab_name or doc.company or frappe.db.get_single_value("Global Defaults", "default_company") or "" }}</div>
		<div class="lab-meta">
			{% if lab.address %}<div>{{ lab.address }}</div>{% endif %}
			<div>
				{% if lab.phone %}电话:{{ lab.phone }}{% endif %}
				{% if lab.email %} &nbsp; 邮箱:{{ lab.email }}{% endif %}
			</div>
			<div>
				{% if lab.cnas_no %}CNAS 认可号:{{ lab.cnas_no }}{% endif %}
				{% if lab.cma_no %} &nbsp; CMA 编号:{{ lab.cma_no }}{% endif %}
			</div>
		</div>
	</div>
	<div class="doc-title">
		<h1>{{ _("检测委托单") }}</h1>
		<div class="doc-no">委托单号:{{ doc.name }}</div>
	</div>
</div>
"""

FOOTER = """
<div class="footer">
	{% if lab.report_disclaimer %}<div>{{ lab.report_disclaimer }}</div>{% endif %}
	<div>{{ lab.lab_name or doc.company or "" }}{% if lab.address %} · {{ lab.address }}{% endif %}{% if lab.phone %} · 电话 {{ lab.phone }}{% endif %}</div>
</div>
"""

TEST_REQUEST_HTML = (
	"""
<div class="print-format">
"""
	+ HEADER
	+ """
	{% set request = doc %}
	{% set consignor = frappe.db.get_value("Customer", doc.customer, "customer_name") or doc.customer %}
	{% set invoicing = frappe.db.get_value("Customer", doc.invoice_customer, "customer_name") if doc.invoice_customer else consignor %}
	{% set reporting = frappe.db.get_value("Customer", doc.report_customer, "customer_name") if doc.report_customer else consignor %}
	<table class="kv">
		<tr>
			<th>委托单位</th><td>{{ consignor }}</td>
			<th>委托日期</th><td>{{ frappe.utils.formatdate(doc.transaction_date) }}</td>
		</tr>
		<tr>
			<th>发票抬头</th><td>{{ invoicing }}{% if not doc.invoice_customer %} <span class="muted">(同委托单位)</span>{% endif %}</td>
			<th>要求完成日期</th><td>{{ frappe.utils.formatdate(doc.required_by) if doc.required_by else "-" }}</td>
		</tr>
		<tr>
			<th>报告抬头</th><td>{{ reporting }}{% if not doc.report_customer %} <span class="muted">(同委托单位)</span>{% endif %}</td>
			<th>客户参考号</th><td>{{ doc.customer_reference or "-" }}</td>
		</tr>
		<tr>
			<th>联系人</th>
			<td>{% if doc.contact %}{{ frappe.db.get_value("Contact", doc.contact, "full_name") or doc.contact }}
				{% set phone = frappe.db.get_value("Contact", doc.contact, "mobile_no") or frappe.db.get_value("Contact", doc.contact, "phone") %}
				{% if phone %} / {{ phone }}{% endif %}{% else %}-{% endif %}</td>
			<th>委托方式 / 样品处置</th>
			<td>{{ doc.entrustment_mode or "-" }} / {{ doc.sample_disposal or "-" }}</td>
		</tr>
	</table>

	<h3>样品清单</h3>
	<table>
		<thead>
			<tr><th style="width:6%">#</th><th>样品名称</th><th>客户样品编号</th><th>规格/型号</th><th>批号/序列号</th><th class="num">数量</th><th>单位</th></tr>
		</thead>
		<tbody>
			{% set samples = frappe.get_all("Sample", filters={"test_request": doc.name}, fields=["name","sample_name","client_sample_code","specification","batch_no","qty","uom"], order_by="sample_name") %}
			{% for s in samples %}
			<tr>
				<td class="center">{{ loop.index }}</td>
				<td>{{ s.sample_name }}</td>
				<td>{{ s.client_sample_code or "-" }}</td>
				<td>{{ s.specification or "-" }}</td>
				<td>{{ s.batch_no or "-" }}</td>
				<td class="num">{{ s.qty }}</td>
				<td>{{ s.uom or "-" }}</td>
			</tr>
			{% endfor %}
			{% if not samples %}<tr><td colspan="7" class="center muted">未登记样品</td></tr>{% endif %}
		</tbody>
	</table>

	<h3>试验项目</h3>
	<table>
		<thead>
			<tr><th style="width:6%">#</th><th>样品</th><th>检测项目</th><th>检测标准</th><th>检测方法</th><th class="num">数量</th><th class="num">时长(h)</th><th class="num">循环</th><th>备注</th></tr>
		</thead>
		<tbody>
			{% for row in doc.items %}
			<tr>
				<td class="center">{{ loop.index }}</td>
				<td>{{ frappe.db.get_value("Sample", row.sample, "sample_name") or row.sample }}</td>
				<td>{{ row.item_name or row.item }}</td>
				<td>{{ frappe.db.get_value("Test Standard", row.standard, "standard_code") if row.standard else "-" }}</td>
				<td>{{ frappe.db.get_value("Test Method", row.test_method, "method_name") if row.test_method else "-" }}</td>
				<td class="num">{{ row.qty }}</td>
				<td class="num">{{ row.hours or "-" }}</td>
				<td class="num">{{ row.cycles or "-" }}</td>
				<td>{{ row.remarks or "" }}{% if row.subcontracted %} 分包:{{ row.subcontractor or "-" }}{% endif %}</td>
			</tr>
			{% endfor %}
		</tbody>
	</table>

	{% if doc.remarks %}<h3>委托备注</h3><div>{{ doc.remarks }}</div>{% endif %}

	<table class="sign">
		<tr>
			<th style="width:12%">委托方确认</th><td style="width:38%"></td>
			<th style="width:12%">受理人</th><td>{{ frappe.db.get_value("User", doc.owner, "full_name") or doc.owner }}</td>
		</tr>
		<tr>
			<th>确认日期</th><td></td>
			<th>受理日期</th><td>{{ frappe.utils.formatdate(doc.transaction_date) }}</td>
		</tr>
	</table>
"""
	+ FOOTER
	+ """
</div>
"""
)

QUOTATION_HTML = (
	"""
<div class="print-format">
"""
	+ HEADER.replace("检测委托单", "检测报价单")
	+ """
	{% set customer_name = frappe.db.get_value("Customer", doc.party_name, "customer_name") or doc.party_name %}
	{% set address = frappe.db.get_value("Address", {"link_doctype": "Customer", "link_name": doc.party_name, "is_primary_address": 1}, "name") %}
	<table class="kv">
		<tr>
			<th>客户</th><td>{{ customer_name }}</td>
			<th>报价单号</th><td>{{ doc.name }}</td>
		</tr>
		<tr>
			<th>联系人</th><td>{{ frappe.db.get_value("Contact", doc.contact_person, "full_name") if doc.contact_person else "-" }}</td>
			<th>报价日期</th><td>{{ frappe.utils.formatdate(doc.transaction_date) }}</td>
		</tr>
		<tr>
			<th>客户参考号</th><td>{{ doc.customer_reference or "-" }}</td>
			<th>有效期至</th><td>{{ frappe.utils.formatdate(doc.valid_till) if doc.valid_till else "-" }}</td>
		</tr>
		{% if doc.lims_test_request %}
		<tr><th>检测委托单</th><td colspan="3">{{ doc.lims_test_request }}</td></tr>
		{% endif %}
		{% if address %}
		<tr><th>地址</th><td colspan="3">{% set a = frappe.get_doc("Address", address) %}{{ [a.address_line1, a.address_line2, a.city, a.state, a.pincode].select() | join(" ") }}</td></tr>
		{% endif %}
	</table>

	<table>
		<thead>
			<tr><th style="width:6%">#</th><th>检测项目 / 说明</th><th class="num">数量</th><th>单位</th><th class="num">单价</th><th class="num">金额</th></tr>
		</thead>
		<tbody>
			{% for row in doc.items %}
			<tr>
				<td class="center">{{ loop.index }}</td>
				<td><b>{{ row.item_name or row.item_code }}</b>{% if row.description %}<div class="muted">{{ row.description }}</div>{% endif %}</td>
				<td class="num">{{ row.qty }}</td>
				<td>{{ row.uom or row.stock_uom or "" }}</td>
				<td class="num">{{ row.get_formatted("rate", doc) }}</td>
				<td class="num">{{ row.get_formatted("amount", doc) }}</td>
			</tr>
			{% endfor %}
		</tbody>
		<tfoot>
			<tr><th colspan="5" class="num">合计</th><th class="num">{{ doc.get_formatted("total") }}</th></tr>
			{% if doc.discount_amount %}
			<tr><th colspan="5" class="num">折扣</th><th class="num">{{ doc.get_formatted("discount_amount") }}</th></tr>
			{% endif %}
			<tr><th colspan="5" class="num">含税总额</th><th class="num">{{ doc.get_formatted("grand_total") }}</th></tr>
		</tfoot>
	</table>

	{% if doc.terms %}
	<h3>报价说明</h3>
	<div>{{ doc.terms }}</div>
	{% endif %}
"""
	+ FOOTER
	+ """
</div>
"""
)

TEST_REPORT_HTML = (
	"""
<div class="print-format">
"""
	+ HEADER.replace("检测委托单", "检测报告")
	+ """
	{% set request = frappe.get_doc("Test Request", doc.test_request) if doc.test_request else None %}
	<table class="kv">
		<tr>
			<th>报告编号</th><td>{{ doc.name }}</td>
			<th>报告日期</th><td>{{ frappe.utils.formatdate(doc.report_date or doc.issued_on) }}</td>
		</tr>
		<tr>
			<th>报告抬头</th><td>{{ frappe.db.get_value("Customer", doc.customer, "customer_name") or doc.customer or "-" }}</td>
			<th>委托单位</th><td>{{ frappe.db.get_value("Customer", request.customer, "customer_name") if request else "-" }}</td>
		</tr>
		<tr>
			<th>委托单号</th><td>{{ doc.test_request or "-" }}</td>
			<th>报告状态</th><td>{{ doc.status }}</td>
		</tr>
		{% if doc.sample %}
		{% set sample = frappe.get_doc("Sample", doc.sample) %}
		<tr>
			<th>样品名称</th><td>{{ sample.sample_name }}</td>
			<th>规格/型号 · 批号</th><td>{{ sample.specification or "-" }} · {{ sample.batch_no or "-" }}</td>
		</tr>
		<tr>
			<th>客户样品编号</th><td>{{ sample.client_sample_code or "-" }}</td>
			<th>收样日期</th><td>{{ frappe.utils.formatdate(sample.received_date) if sample.received_date else "-" }}</td>
		</tr>
		{% endif %}
	</table>

	<h3>检测结果</h3>
	<table>
		<thead>
			<tr><th style="width:5%">#</th><th>检测项目</th><th>检测标准 / 条款</th><th>技术要求</th><th>实测结果</th><th style="width:8%">判定</th><th>设备</th></tr>
		</thead>
		<tbody>
			{% for row in doc.items %}
			<tr>
				<td class="center">{{ loop.index }}</td>
				<td>{{ frappe.db.get_value("Item", row.item, "item_name") or row.item }}
					{% if row.sample %}<div class="muted">样品:{{ frappe.db.get_value("Sample", row.sample, "sample_name") or row.sample }}</div>{% endif %}
				</td>
				<td>{{ frappe.db.get_value("Test Standard", row.standard, "standard_code") if row.standard else "-" }}{% if row.standard_clause %} / {{ row.standard_clause }}{% endif %}</td>
				<td>{{ row.requirement or "-" }}</td>
				<td>{{ row.result or "-" }}</td>
				<td class="center">{{ row.verdict or "-" }}</td>
				<td>{{ frappe.db.get_value("Asset", row.equipment, "asset_name") if row.equipment else "-" }}</td>
			</tr>
			{% endfor %}
			{% if not doc.items %}<tr><td colspan="7" class="center muted">无检测项目</td></tr>{% endif %}
		</tbody>
	</table>

	<h3>检测结论</h3>
	<div>{{ doc.conclusion or "-" }}</div>

	<table class="sign">
		<tr>
			<th style="width:12%">检测人</th><td>{{ frappe.db.get_value("User", doc.tested_by, "full_name") if doc.tested_by else "" }}</td>
			<th style="width:12%">审核人</th><td>{{ frappe.db.get_value("User", doc.reviewed_by, "full_name") if doc.reviewed_by else "" }}</td>
			<th style="width:12%">批准人</th><td>{{ frappe.db.get_value("User", doc.approved_by, "full_name") if doc.approved_by else "" }}</td>
		</tr>
		<tr>
			<th>检测日期</th><td>{{ frappe.utils.formatdate(doc.report_date) if doc.report_date else "" }}</td>
			<th>审核日期</th><td>{{ frappe.utils.formatdate(doc.reviewed_on) if doc.reviewed_on else "" }}</td>
			<th>签发日期</th><td>{{ frappe.utils.formatdate(doc.issued_on) if doc.issued_on else "" }}</td>
		</tr>
	</table>
"""
	+ FOOTER
	+ """
</div>
"""
)

FORMATS = {
	"检测委托单": "Test Request",
	"检测报价单": "Quotation",
	"检测报告": "Test Report",
}

HTML = {
	"检测委托单": TEST_REQUEST_HTML,
	"检测报价单": QUOTATION_HTML,
	"检测报告": TEST_REPORT_HTML,
}


def write_format(name, doc_type):
	doc = {
		"absolute_value": 0,
		"align_labels_right": 0,
		"creation": CREATED,
		"css": CSS.strip(),
		"custom_format": 1,
		"disabled": 0,
		"doc_type": doc_type,
		"docstatus": 0,
		"doctype": "Print Format",
		"font_size": 12,
		"html": HTML[name].strip(),
		"idx": 0,
		"line_breaks": 0,
		"margin_bottom": 15.0,
		"margin_left": 15.0,
		"margin_right": 15.0,
		"margin_top": 15.0,
		"modified": TS,
		"modified_by": "Administrator",
		"module": "Testing",
		"name": name,
		"owner": "Administrator",
		"page_number": "Hide",
		"pdf_generator": "wkhtmltopdf",
		"print_format_builder": 0,
		"print_format_builder_beta": 0,
		"print_format_for": "DocType",
		"print_format_type": "Jinja",
		"raw_printing": 0,
		"show_section_headings": 0,
		"standard": "Yes",
	}
	path = os.path.join(ROOT, "testing", "print_format", name, f"{name}.json")
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		fh.write(json.dumps(doc, indent="\t", sort_keys=True, ensure_ascii=False) + "\n")
	print("wrote", path)


for fmt_name, fmt_doc_type in FORMATS.items():
	write_format(fmt_name, fmt_doc_type)
