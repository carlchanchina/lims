<template>
	<MasterCrud
		title="报价目录"
		singular="目录"
		:columns="['catalog_code', 'catalog_name', 'item', 'standard', 'equipment', 'price', 'tat_days', 'enabled']"
		:fields="fields"
		:load="apiMethods.catalogList"
		:save="apiMethods.catalogSave"
		:remove="apiMethods.catalogDelete"
		:new-row="newRow"
		action-label="设为默认"
		:action="apiMethods.catalogSetDefault"
	/>
</template>

<script setup>
import { onMounted, ref } from "vue";
import MasterCrud from "../components/MasterCrud.vue";
import { apiMethods } from "../api";

const items = ref([]);
const standards = ref([]);
const equipment = ref([]);

onMounted(async () => {
	items.value = (await apiMethods.itemSearch("")) || [];
	standards.value = ((await apiMethods.standardsList({})) || []).map((d) => ({
		value: d.name,
		label: d.standard_code,
	}));
	equipment.value = ((await apiMethods.equipmentList({})) || []).map((d) => ({
		value: d.name,
		label: `${d.equipment_code} - ${d.equipment_name}`,
	}));
	fields.value = fields.value.map((field) => {
		if (field.fieldname === "item") return { ...field, options: items.value };
		if (field.fieldname === "standard") return { ...field, options: standards.value };
		if (field.fieldname === "equipment") return { ...field, options: equipment.value };
		return field;
	});
});

const fields = ref([
	{ fieldname: "catalog_code", label: "目录编码", type: "text" },
	{ fieldname: "catalog_name", label: "目录名称", type: "text" },
	{ fieldname: "item", label: "检测项目", type: "datalist", options: [] },
	{ fieldname: "standard", label: "检测标准", type: "select", options: [] },
	{ fieldname: "equipment", label: "设备", type: "select", options: [] },
	{ fieldname: "price", label: "价格", type: "number" },
	{ fieldname: "uom", label: "单位", type: "text" },
	{ fieldname: "tat_days", label: "周期(天)", type: "number" },
	{ fieldname: "is_default", label: "默认报价项", type: "checkbox", help: "设为该 item+standard 的默认目录" },
	{ fieldname: "enabled", label: "启用", type: "checkbox", help: "启用" },
	{ fieldname: "remarks", label: "备注", type: "textarea" },
]);

function newRow() {
	return {
		catalog_code: "",
		catalog_name: "",
		item: "",
		standard: "",
		equipment: "",
		price: 0,
		uom: "次",
		tat_days: 1,
		is_default: 0,
		enabled: 1,
		remarks: "",
	};
}
</script>
