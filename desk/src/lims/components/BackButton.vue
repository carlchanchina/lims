<template>
	<Button
		variant="ghost"
		icon-left="lucide-chevron-left"
		:label="label"
		class="!justify-start truncate font-medium text-ink-gray-8 hover:bg-transparent hover:opacity-70 ps-1"
		@click="$emit('back')"
	/>
</template>

<script setup>
import { Button } from "frappe-ui";

defineProps({ label: { type: String, default: "返回" } });
defineEmits(["back"]);
</script>
