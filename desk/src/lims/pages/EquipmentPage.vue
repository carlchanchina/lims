<template>
	<MasterCrud
		title="设备"
		singular="设备"
		:columns="['equipment_code', 'equipment_name', 'model', 'status']"
		:fields="fields"
		:load="apiMethods.equipmentList"
		:save="apiMethods.equipmentSave"
		:remove="apiMethods.equipmentDelete"
		:new-row="newRow"
	/>
</template>

<script setup>
import MasterCrud from "../components/MasterCrud.vue";
import { apiMethods } from "../api";

const fields = [
	{ fieldname: "equipment_code", label: "设备编码", type: "text" },
	{ fieldname: "equipment_name", label: "设备名称", type: "text" },
	{ fieldname: "model", label: "型号/规格", type: "text" },
	{ fieldname: "status", label: "设备状态", type: "select", options: ["可用", "维修中", "停用"] },
	{ fieldname: "remarks", label: "备注", type: "textarea" },
];

function newRow() {
	return { equipment_code: "", equipment_name: "", model: "", status: "可用", remarks: "" };
}
</script>
