app_name = "test"
app_title = "Testing"
app_publisher = "Carl"
app_description = "环境试验 LIMS - 以 ERPNext 为事实源的自定义业务 App"
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
		"logo": "/assets/test/images/lims.svg",
		"title": "环境试验 LIMS",
		"route": "/lims",
		"has_permission": "test.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/test/css/test.css"
# app_include_js = "/assets/test/js/test.js"

# include js, css files in header of web template
# web_include_css = "/assets/test/css/test.css"
# web_include_js = "/assets/test/js/test.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "test/public/scss/website"

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
# app_include_icons = "test/public/icons.svg"

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
# 	"methods": "test.utils.jinja_methods",
# 	"filters": "test.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "test.setup.install.after_install"
after_migrate = ["test.setup.install.run_schema_cleanup"]

# Uninstallation
# ------------

# before_uninstall = "test.uninstall.before_uninstall"
# after_uninstall = "test.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "test.utils.before_app_install"
# after_app_install = "test.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "test.utils.before_app_uninstall"
# after_app_uninstall = "test.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "test.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "test.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["test.search.awesomebar_results"]

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
	"Customer": {
		"after_insert": "test.integrations.erpnext_party.sync_customer",
		"on_update": "test.integrations.erpnext_party.sync_customer",
		"after_rename": "test.integrations.erpnext_party.rename_customer",
		"on_trash": "test.integrations.erpnext_party.delete_customer",
	},
	"Contact": {
		"after_insert": "test.integrations.erpnext_party.sync_contact",
		"on_update": "test.integrations.erpnext_party.sync_contact",
		"after_rename": "test.integrations.erpnext_party.rename_contact",
		"on_trash": "test.integrations.erpnext_party.delete_contact",
	},
	# 请求上的"报价/订单/报告"三个派生状态,跟着源单据动。
	"Quotation": {
		"on_update": "test.testing.doctype.test_request.test_request.sync_request_quotation_status",
		"on_submit": "test.testing.doctype.test_request.test_request.sync_request_quotation_status",
		"on_cancel": "test.testing.doctype.test_request.test_request.sync_request_quotation_status",
	},
	"Sales Order": {
		"on_update": "test.testing.doctype.test_request.test_request.sync_request_sales_order_status",
		"on_submit": "test.testing.doctype.test_request.test_request.sync_request_sales_order_status",
		"on_cancel": "test.testing.doctype.test_request.test_request.sync_request_sales_order_status",
	},
	"Test Report": {
		"after_insert": "test.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_update": "test.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_trash": "test.testing.doctype.test_request.test_request.sync_request_report_status",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"test.tasks.all"
# 	],
# 	"daily": [
# 		"test.tasks.daily"
# 	],
# 	"hourly": [
# 		"test.tasks.hourly"
# 	],
# 	"weekly": [
# 		"test.tasks.weekly"
# 	],
# 	"monthly": [
# 		"test.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "test.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "test.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "test.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "test.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["test.utils.before_request"]
# after_request = ["test.utils.after_request"]

# Job Events
# ----------
# before_job = ["test.utils.before_job"]
# after_job = ["test.utils.after_job"]

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
# 	"test.auth.validate"
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
