<template>
	<FrappeUIProvider>
		<LimsLayout>
			<RouterView class="flex flex-1 flex-col overflow-auto" />
		</LimsLayout>
	</FrappeUIProvider>
</template>

<script setup>
import { FrappeUIProvider } from "frappe-ui";
import { RouterView } from "vue-router";
import LimsLayout from "./LimsLayout.vue";
</script>
