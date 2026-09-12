app_name = "lims"
app_title = "旭博检测中心OS"
app_publisher = "Carl"
app_description = "旭博检测中心OS - 以 ERPNext 为事实源的检测中心一体化业务 App"
app_email = "cowin3332@gmail.com"
app_license = "mit"
app_icon = "octicon octicon-checklist"
app_color = "green"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "lims",
		"logo": "/assets/lims/images/lims.svg",
		"title": "旭博检测中心OS",
		"route": "/desk/首页",
		"has_permission": "lims.api.permission.has_app_permission",
	}
]

# DocTypes whose documents live in this app's module folders and are re-imported
# on every migrate. Number Cards / Dashboard Charts for the desks ship as files
# under lims/testing/<doctype>/<name>/<name>.json.
importable_doctypes = ["Number Card", "Dashboard Chart"]

# 客户门户(erpnext-nuxt):客户联系人登录后,只能看自己公司的单据。
has_website_permission = {
	"Test Request": "lims.api.portal.website_permission_for_customer_doc",
	"Test Report": "lims.api.portal.website_permission_for_customer_doc",
	"Quotation": "lims.api.portal.website_permission_for_customer_doc",
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lims/css/lims.css"
# app_include_js = "/assets/lims/js/lims.js"

# include js, css files in header of web template
# web_include_css = "/assets/lims/css/lims.css"
# web_include_js = "/assets/lims/js/lims.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lims/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lims/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lims.utils.jinja_methods",
# 	"filters": "lims.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "lims.setup.install.after_install"
after_migrate = [
	"lims.setup.install.run_schema_cleanup",
	"lims.setup.detection_os.setup_detection_os",
]

# Uninstallation
# ------------

# before_uninstall = "lims.uninstall.before_uninstall"
# after_uninstall = "lims.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lims.utils.before_app_install"
# after_app_install = "lims.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lims.utils.before_app_uninstall"
# after_app_uninstall = "lims.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lims.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lims.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["lims.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------

doc_events = {
	# 方向约定:单向 LIMS → ERPNext。LIMS 不反向同步 ERPNext 主数据,
	# 客户/联系人/报价/订单都直接以 ERPNext 为事实源(LIMS 只读 + 定制字段)。
	# 客户校验:统一社会信用代码(税号)格式与唯一性,见 erpnext_masters.validate_customer。
	"Customer": {
		"validate": "lims.integrations.erpnext_masters.validate_customer",
	},
	# 委托请求保存后自动生成 ERPNext Project,测试项同步为 Project Task。
	"Test Request": {
		"after_insert": "lims.integrations.erpnext_projects.create_project_from_request",
		"on_update": "lims.integrations.erpnext_projects.sync_tasks",
	},
	# Test Report 是 LIMS 自己的单据,报告状态联动委托请求(LIMS 内部,非 ERPNext 回写)。
	"Test Report": {
		"after_insert": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_update": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_trash": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
	},
	# 请求上的「报价/订单」派生状态跟着 ERPNext 源单据走。
	"Quotation": {
		"on_update": "lims.testing.doctype.test_request.test_request.sync_request_quotation_status",
		"on_submit": "lims.testing.doctype.test_request.test_request.sync_request_quotation_status",
		"on_cancel": "lims.testing.doctype.test_request.test_request.sync_request_quotation_status",
		"on_trash": "lims.testing.doctype.test_request.test_request.sync_request_quotation_status",
	},
	"Sales Order": {
		"on_update": "lims.testing.doctype.test_request.test_request.sync_request_sales_order_status",
		"on_submit": "lims.testing.doctype.test_request.test_request.sync_request_sales_order_status",
		"on_cancel": "lims.testing.doctype.test_request.test_request.sync_request_sales_order_status",
		"on_trash": "lims.testing.doctype.test_request.test_request.sync_request_sales_order_status",
	},
	# 校准记录回写 Asset 上的校准快照(设备使用登记据此拦截过期设备)。
	"Calibration Record": {
		"after_insert": "lims.testing.doctype.calibration_record.calibration_record.sync_asset_calibration",
		"on_update": "lims.testing.doctype.calibration_record.calibration_record.sync_asset_calibration",
		"on_trash": "lims.testing.doctype.calibration_record.calibration_record.sync_asset_calibration",
	},
}

# Custom Fields
# -------------
# ERPNext DocType 上的 lims_* 定制字段由 lims.setup.install.create_custom_fields 创建
# (Frappe 不会读取 hooks 里的 custom_fields,详见 lims/setup/install.py)。

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lims.tasks.all"
# 	],
# 	"daily": [
# 		"lims.tasks.daily"
# 	],
# 	"hourly": [
# 		"lims.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lims.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lims.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lims.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lims.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lims.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lims.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lims.utils.before_request"]
# after_request = ["lims.utils.after_request"]

# Job Events
# ----------
# before_job = ["lims.utils.before_job"]
# after_job = ["lims.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lims.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
