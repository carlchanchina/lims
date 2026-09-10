<template>
	<span ref="target" class="relative">
		<span
			v-if="unreadCount"
			class="pointer-events-none absolute right-1 top-1 z-10 size-1.5 rounded-full bg-surface-blue-5"
		/>
		<Button
			variant="ghost"
			icon="lucide-bell"
			class="!text-ink-gray-7"
			@click="toggle"
		/>
		<span
			v-if="open"
			class="absolute right-0 top-10 z-30 w-[360px] overflow-hidden rounded-xl border border-outline-gray-1 bg-surface-base shadow-lg"
		>
			<div class="flex items-center justify-between border-b px-4 py-2.5">
				<span class="text-lg-medium text-ink-gray-9">通知</span>
				<Button
					v-if="items.length"
					theme="gray"
					variant="ghost"
					@click="markAllRead"
				>
					全部已读
				</Button>
			</div>
			<div v-if="items.length" class="max-h-[420px] divide-y overflow-y-auto">
				<button
					v-for="item in items"
					:key="item.id"
					class="flex w-full items-start gap-3 px-4 py-3 text-start hover:bg-surface-gray-2"
					@click="openItem(item)"
				>
					<span
						class="mt-1 size-1.5 shrink-0 rounded-full"
						:class="isRead(item) ? 'bg-transparent' : 'bg-surface-blue-5'"
					/>
					<span class="min-w-0">
						<span class="block truncate font-medium text-ink-gray-9">{{ item.title }}</span>
						<span class="mt-0.5 block text-sm text-ink-gray-6">{{ item.description }}</span>
					</span>
				</button>
			</div>
			<div v-else class="p-8 text-center text-ink-gray-5">
				<component :is="BellIcon" class="mx-auto mb-2 size-6" />
				暂无待处理事项
			</div>
		</span>
	</span>
</template>

<script setup>
import { Button } from "frappe-ui";
import { onClickOutside } from "@vueuse/core";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import BellIcon from "~icons/lucide/bell";
import { apiMethods } from "../api";

const router = useRouter();
const target = ref(null);
const open = ref(false);
const items = ref([]);
const readIds = ref(new Set(JSON.parse(localStorage.getItem("lims_notifications_read") || "[]")));

const unreadCount = computed(() => items.value.filter((item) => !isRead(item)).length);

onMounted(refresh);
onClickOutside(target, () => (open.value = false));

async function refresh() {
	items.value = (await apiMethods.notifications()) || [];
}

function toggle() {
	open.value = !open.value;
	if (open.value) refresh();
}

function isRead(item) {
	return readIds.value.has(item.id);
}

function saveRead() {
	localStorage.setItem(
		"lims_notifications_read",
		JSON.stringify([...readIds.value].slice(-200))
	);
}

function openItem(item) {
	readIds.value.add(item.id);
	saveRead();
	open.value = false;
	router.push(item.route);
}

function markAllRead() {
	items.value.forEach((item) => readIds.value.add(item.id));
	saveRead();
}
</script>
