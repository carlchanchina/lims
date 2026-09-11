<template>
	<MasterCrud
		title="测试标准"
		singular="标准"
		:columns="['standard_code', 'standard_name', 'version', 'organization', 'status']"
		:fields="fields"
		:load="apiMethods.standardsList"
		:save="apiMethods.standardSave"
		:remove="apiMethods.standardDelete"
		:new-row="newRow"
	/>
</template>

<script setup>
import MasterCrud from "../components/MasterCrud.vue";
import { apiMethods } from "../api";

const fields = [
	{ fieldname: "standard_code", label: "标准编码", type: "text" },
	{ fieldname: "standard_name", label: "标准名称", type: "text" },
	{ fieldname: "version", label: "版本/年份", type: "text", help: "如 2008 / 2023" },
	{ fieldname: "organization", label: "发布/归口单位", type: "text" },
	{ fieldname: "effective_date", label: "实施日期", type: "date" },
	{ fieldname: "superseded_by", label: "被替代为", type: "text" },
	{
		fieldname: "status",
		label: "标准状态",
		type: "select",
		options: ["现行", "废止", "被替代"],
	},
	{ fieldname: "remarks", label: "备注", type: "textarea" },
];

function newRow() {
	return {
		standard_code: "",
		standard_name: "",
		version: "",
		organization: "",
		effective_date: "",
		superseded_by: "",
		status: "现行",
		remarks: "",
	};
}
</script>
