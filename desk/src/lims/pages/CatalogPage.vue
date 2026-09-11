<template>
	<div class="p-6">
		<p class="mb-4 text-sm text-ink-gray-5">
			协议价 = 检测项目的约定价格,按 <b>客户</b> 或 <b>行业</b> 约定(都留空即通用价)。
			生成报价时按 客户协议价 → 行业协议价 → 通用协议价 的顺序取价。
		</p>
		<MasterCrud
			title="协议价"
			singular="协议价"
			:columns="[
				'catalog_code',
				'catalog_name',
				'item',
				'customer',
				'industry',
				'price',
				'tat_days',
				'enabled',
			]"
			:fields="fields"
			:load="apiMethods.catalogList"
			:save="apiMethods.catalogSave"
			:remove="apiMethods.catalogDelete"
			:new-row="newRow"
		/>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import MasterCrud from "../components/MasterCrud.vue";
import {
	customerFields,
	customerPayload,
	industryFields,
	itemFields,
} from "../masterForms";
import { apiMethods } from "../api";

const items = ref([]);
const customers = ref([]);
const industries = ref([]);
const itemOptions = ref({ item_groups: [], uoms: [], defaults: {} });
const partyOptions = ref({
	customer_types: [],
	customer_groups: [],
	territories: [],
	industries: [],
	defaults: {},
});

const fields = computed(() => [
	{ fieldname: "catalog_code", label: "协议编号", type: "text" },
	{ fieldname: "catalog_name", label: "协议价名称", type: "text" },
	{
		fieldname: "item",
		label: "检测项目",
		type: "datalist",
		options: items.value,
		create: {
			label: "+ 新建",
			title: "新建检测项目(写入 ERPNext Item)",
			fields: itemFields(itemOptions.value),
			save: (payload) => apiMethods.itemCreate(payload),
			onCreated: loadItems,
		},
	},
	{
		fieldname: "customer",
		label: "客户",
		type: "select",
		options: customers.value,
		create: {
			label: "+ 新建",
			title: "新建客户(写入 ERPNext)",
			fields: customerFields(partyOptions.value),
			save: (payload) => apiMethods.customerCreate(customerPayload(payload)),
			onCreated: loadCustomers,
		},
	},
	{
		fieldname: "industry",
		label: "行业",
		type: "select",
		options: industries.value,
		create: {
			label: "+ 新建",
			title: "新建行业",
			fields: industryFields(),
			save: (payload) => apiMethods.industryCreate(payload),
			onCreated: loadIndustries,
		},
	},
	{ fieldname: "price", label: "协议价", type: "number" },
	{ fieldname: "uom", label: "单位", type: "text" },
	{ fieldname: "tat_days", label: "周期(天)", type: "number" },
	{ fieldname: "enabled", label: "启用", type: "checkbox", help: "启用" },
	{ fieldname: "remarks", label: "备注", type: "textarea" },
]);

onMounted(loadOptions);

async function loadOptions() {
	const [itemList, customerList, industryList, iOptions, pOptions] =
		await Promise.all([
			apiMethods.itemSearch(""),
			apiMethods.customerSearch(""),
			apiMethods.industryList(),
			apiMethods.itemFormOptions(),
			apiMethods.partyFormOptions(),
		]);
	items.value = itemList || [];
	customers.value = customerList || [];
	industries.value = toOptions(industryList);
	itemOptions.value = iOptions || itemOptions.value;
	partyOptions.value = pOptions || partyOptions.value;
}

function toOptions(rows) {
	return (rows || []).map((row) => ({
		value: row.name,
		label: row.industry_name || row.name,
	}));
}

async function loadItems() {
	items.value = (await apiMethods.itemSearch("")) || [];
}

async function loadCustomers() {
	customers.value = (await apiMethods.customerSearch("")) || [];
}

async function loadIndustries() {
	industries.value = toOptions(await apiMethods.industryList());
}

function newRow() {
	return {
		catalog_code: "",
		catalog_name: "",
		item: "",
		customer: "",
		industry: "",
		price: 0,
		uom: "次",
		tat_days: 1,
		enabled: 1,
		remarks: "",
	};
}
</script>
