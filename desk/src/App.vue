<template>
	<div class="flex h-full">
		<AppSidebar />
		<main class="flex-1 min-w-0 overflow-y-auto bg-surface-gray-2">
			<RouterView />
		</main>
	</div>
</template>

<script setup>
import AppSidebar from "./components/AppSidebar.vue";
import { RouterView } from "vue-router";
</script>
