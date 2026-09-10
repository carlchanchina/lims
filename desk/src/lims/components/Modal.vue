<template>
	<div
		class="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50"
		@click.self="$emit('close')"
	>
		<div class="bg-white rounded-xl w-full max-w-lg p-5">
			<div class="flex justify-between items-center mb-3">
				<h2 class="text-lg font-semibold">{{ title }}</h2>
				<button class="text-gray-400 hover:text-gray-700" @click="$emit('close')">✕</button>
			</div>
			<slot />
		</div>
	</div>
</template>

<script setup>
defineProps({ title: String });
defineEmits(["close"]);
</script>
