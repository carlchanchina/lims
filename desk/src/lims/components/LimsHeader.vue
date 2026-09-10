<template>
	<header class="flex h-10.5 items-center justify-between gap-2 border-b border-outline-gray-1 px-4">
		<div class="flex min-w-0 flex-1 items-center gap-2">
			<BackButton
				v-if="showBack"
				:label="backLabel"
				@back="router.back()"
			/>
			<div class="truncate text-lg-medium text-ink-gray-9">{{ title }}</div>
		</div>
		<div class="flex shrink-0 items-center gap-2">
			<slot name="actions" />
		</div>
	</header>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import BackButton from "./BackButton.vue";

const route = useRoute();
const router = useRouter();

const title = computed(() => route.meta.title || "环境试验 LIMS");
const showBack = computed(() => !!route.meta.back);
const backLabel = computed(() => route.meta.parentTitle || "返回");
</script>
