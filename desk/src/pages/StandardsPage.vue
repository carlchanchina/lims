<template>
	<MasterCrud
		title="测试标准"
		singular="标准"
		:columns="['standard_code', 'standard_name', 'organization', 'status']"
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
	{ fieldname: "organization", label: "发布/归口单位", type: "text" },
	{ fieldname: "status", label: "标准状态", type: "select", options: ["现行", "废止"] },
	{ fieldname: "remarks", label: "备注", type: "textarea" },
];

function newRow() {
	return { standard_code: "", standard_name: "", organization: "", status: "现行", remarks: "" };
}
</script>
