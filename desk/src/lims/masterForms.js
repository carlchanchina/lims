// 主数据"新建"表单的字段定义与提交载荷,客户/联系人/设备/行业在多个页面复用。

export function customerFields(options = {}) {
	return [
		{ fieldname: "customer_name", label: "客户名称", required: true },
		{
			fieldname: "customer_type",
			label: "客户类型",
			type: "select",
			options: options.customer_types || [],
			default: "Company",
		},
		{
			fieldname: "industry",
			label: "行业",
			type: "select",
			options: options.industries || [],
			hint: "用于匹配行业协议价",
		},
		{
			fieldname: "customer_group",
			label: "客户分组",
			type: "select",
			options: options.customer_groups || [],
			default: options.defaults?.customer_group,
		},
		{
			fieldname: "territory",
			label: "地区",
			type: "select",
			options: options.territories || [],
			default: options.defaults?.territory,
		},
		{ fieldname: "contact_first_name", label: "主要联系人姓名" },
		{ fieldname: "contact_email", label: "主要联系人邮箱" },
		{ fieldname: "contact_phone", label: "主要联系人电话" },
	];
}

export function customerPayload(payload = {}) {
	return {
		customer_name: payload.customer_name,
		customer_type: payload.customer_type,
		customer_group: payload.customer_group,
		territory: payload.territory,
		industry: payload.industry,
		contact: {
			first_name: payload.contact_first_name,
			email: payload.contact_email,
			phone: payload.contact_phone,
		},
	};
}

export function assetFields(options = {}) {
	return [
		{ fieldname: "asset_name", label: "设备名称", required: true },
		{
			fieldname: "item_code",
			label: "资产项目(Item)",
			type: "select",
			required: true,
			options: (options.items || []).map((item) => ({
				value: item.name,
				label: `${item.name} - ${item.item_name || ""}`,
			})),
			hint: "只能选 ERPNext 里勾了「固定资产」的非库存物料",
		},
		{
			fieldname: "company",
			label: "公司",
			type: "select",
			required: true,
			options: options.companies || [],
			default: options.defaults?.company,
		},
		{
			fieldname: "location",
			label: "位置",
			type: "select",
			required: true,
			options: options.locations || [],
		},
		{
			fieldname: "custodian",
			label: "保管人",
			type: "select",
			options: (options.custodians || []).map((employee) => ({
				value: employee.name,
				label: employee.employee_name || employee.name,
			})),
		},
		{
			fieldname: "gross_purchase_amount",
			label: "购置金额",
			type: "number",
			required: true,
			hint: "ERPNext 的 Asset 必须要填,没有准确金额可填个估值",
		},
		{
			fieldname: "purchase_date",
			label: "购置日期",
			type: "date",
			default: new Date().toISOString().slice(0, 10),
		},
	];
}

export function industryFields() {
	return [
		{ fieldname: "industry_name", label: "行业名称", required: true },
		{ fieldname: "remarks", label: "备注", type: "textarea" },
	];
}

export function itemFields(options = {}) {
	return [
		{ fieldname: "item_code", label: "项目编码", hint: "留空则用项目名称" },
		{ fieldname: "item_name", label: "项目名称", required: true },
		{
			fieldname: "item_group",
			label: "项目分组",
			type: "select",
			required: true,
			options: options.item_groups || [],
			default: options.defaults?.item_group,
		},
		{
			fieldname: "uom",
			label: "单位",
			type: "select",
			options: options.uoms || [],
			default: options.defaults?.uom,
		},
		{ fieldname: "description", label: "说明", type: "textarea" },
	];
}
