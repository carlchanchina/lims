<template>
	<div class="flex h-screen w-screen bg-surface-base">
		<Sidebar
			v-model:collapsed="collapsed"
			class="border-e border-outline-gray-1"
		>
			<div class="flex h-full flex-col p-2">
				<div class="flex h-12 items-center px-2">
					<div
						class="grid size-8 place-items-center rounded-lg bg-surface-gray-7 text-base font-semibold text-white"
					>
						L
					</div>
					<div v-if="!collapsed" class="ms-2 min-w-0">
						<div class="truncate text-base-medium leading-none text-ink-gray-9">
							环境试验 LIMS
						</div>
						<div class="mt-1 truncate text-sm text-ink-gray-6">
							{{ boot.session_user }}
						</div>
					</div>
				</div>

				<ScrollArea class="mt-3 min-h-0 flex-1 -mx-2" viewport-class="px-2">
					<nav class="flex flex-col gap-0.5">
						<SidebarItem
							v-for="item in items"
							:key="item.to"
							:label="item.label"
							:active="isActive(item.to)"
							@click="router.push(item.to)"
						>
							<template #prefix>
								<component :is="item.icon" class="size-4" />
							</template>
						</SidebarItem>
					</nav>
				</ScrollArea>

				<div class="mt-auto flex flex-col gap-2">
					<SidebarItem :label="__('Log out')" @click="logout">
						<template #prefix>
							<component :is="LogOut" class="size-4" />
						</template>
					</SidebarItem>
					<SidebarCollapseToggle />
				</div>
			</div>
		</Sidebar>

		<div class="flex h-full flex-1 flex-col overflow-auto relative">
			<div class="flex border-b border-outline-gray-1 pe-5">
				<div id="app-header" class="flex-1 w-full"></div>
			</div>
			<slot />
		</div>
	</div>
</template>

<script setup>
import { ScrollArea, Sidebar, SidebarCollapseToggle, SidebarItem } from "frappe-ui";
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import ClipboardList from "~icons/lucide/clipboard-list";
import FolderKanban from "~icons/lucide/folder-kanban";
import BookOpen from "~icons/lucide/book-open";
import LayoutDashboard from "~icons/lucide/layout-dashboard";
import LogOut from "~icons/lucide/log-out";
import Wrench from "~icons/lucide/wrench";
import FileText from "~icons/lucide/file-text";
import { getBoot } from "./boot";

const route = useRoute();
const router = useRouter();
const boot = getBoot();
const collapsed = ref(false);
const __ = (text) => text;

const items = [
	{ label: "仪表盘", to: "/lims/dashboard", icon: LayoutDashboard },
	{ label: "检测请求", to: "/lims/requests", icon: ClipboardList },
	{ label: "检测报告", to: "/lims/reports", icon: FileText },
	{ label: "测试标准", to: "/lims/standards", icon: BookOpen },
	{ label: "设备", to: "/lims/equipment", icon: Wrench },
	{ label: "报价目录", to: "/lims/catalog", icon: FolderKanban },
];

const active = computed(() => route.path);

function isActive(to) {
	return active.value.startsWith(to);
}

function logout() {
	window.location.href = "/api/method/logout";
}
</script>
