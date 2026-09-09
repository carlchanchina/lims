<template>
	<span
		:class="
			'px-2 py-0.5 rounded text-xs font-medium ' +
			colors[status] +
			' ' +
			(colorClass || '')
		"
	>
		{{ label || status }}
	</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	status: { type: String, default: "" },
	label: { type: String, default: "" },
	color: { type: String, default: "" },
});

const defaults = {
	草稿: "bg-gray-100 text-gray-700",
	已报价: "bg-blue-100 text-blue-700",
	待检测: "bg-amber-100 text-amber-700",
	检测中: "bg-indigo-100 text-indigo-700",
	已完成: "bg-emerald-100 text-emerald-700",
	已取消: "bg-red-100 text-red-700",
	已出具: "bg-emerald-100 text-emerald-700",
	已收样: "bg-blue-100 text-blue-700",
	现行: "bg-emerald-100 text-emerald-700",
	废止: "bg-gray-200 text-gray-600",
	可用: "bg-emerald-100 text-emerald-700",
	维修中: "bg-amber-100 text-amber-700",
	停用: "bg-red-100 text-red-700",
};

const colors = computed(() => ({ ...defaults, [props.status]: props.color || defaults[props.status] || "bg-gray-100 text-gray-700" }));
</script>
