<template>
	<Modal v-if="open" title="搜索" @close="close">
		<input
			ref="input"
			v-model="query"
			placeholder="搜索检测请求、样品、报告、目录、标准、设备…"
			class="w-full rounded-lg border border-outline-gray-2 px-3 py-2 text-base outline-none focus:border-outline-gray-4"
			@input="onInput"
		/>
		<div class="mt-3 max-h-[420px] overflow-y-auto">
			<div v-if="loading" class="p-4 text-center text-ink-gray-5">搜索中…</div>
			<div
				v-else-if="query.length >= 2 && !results.length"
				class="p-6 text-center text-ink-gray-5"
			>
				没有匹配结果
			</div>
			<button
				v-for="row in results"
				:key="row.doctype + row.name"
				class="flex w-full items-start gap-3 rounded-lg px-3 py-2 text-start hover:bg-surface-gray-2"
				@click="go(row)"
			>
				<Badge theme="gray" variant="subtle">{{ row.doctype }}</Badge>
				<span class="min-w-0">
					<span class="block truncate font-medium text-ink-gray-9">{{ row.title }}</span>
					<span class="block truncate text-sm text-ink-gray-6">{{ row.subtitle }}</span>
				</span>
			</button>
		</div>
	</Modal>
</template>

<script setup>
import { Badge } from "frappe-ui";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { apiMethods } from "../api";
import Modal from "./Modal.vue";

const router = useRouter();
const open = ref(false);
const query = ref("");
const results = ref([]);
const loading = ref(false);
const input = ref(null);
let timer = null;

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));

function onKeydown(event) {
	if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
		event.preventDefault();
		open.value = true;
		nextTick(() => input.value?.focus());
	}
}

function onInput() {
	clearTimeout(timer);
	timer = setTimeout(async () => {
		if (query.value.trim().length < 2) {
			results.value = [];
			return;
		}
		loading.value = true;
		try {
			results.value = (await apiMethods.globalSearch(query.value.trim())) || [];
		} finally {
			loading.value = false;
		}
	}, 250);
}

function go(row) {
	open.value = false;
	query.value = "";
	results.value = [];
	router.push(row.route);
}

function close() {
	open.value = false;
	query.value = "";
	results.value = [];
}

function openSearch() {
	open.value = true;
	nextTick(() => input.value?.focus());
}

defineExpose({ openSearch });
</script>
