<template>
	<div class="flex h-screen w-screen bg-surface-base">
		<Sidebar
			v-model:collapsed="collapsed"
			class="border-e border-outline-gray-1"
		>
			<div class="flex h-full flex-col p-2">
				<UserMenu :collapsed="collapsed" />

				<ScrollArea class="mt-3 min-h-0 flex-1 -mx-2" viewport-class="px-2">
					<nav class="flex flex-col gap-0.5">
						<LimsTools :collapsed="collapsed" />
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
					<SidebarCollapseToggle />
				</div>
			</div>
		</Sidebar>

		<div class="flex h-full flex-1 flex-col overflow-auto relative">
			<LimsHeader />
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
import CalendarClock from "~icons/lucide/calendar-clock";
import Package from "~icons/lucide/package";
import Users from "~icons/lucide/users";
import Wrench from "~icons/lucide/wrench";
import FileText from "~icons/lucide/file-text";
import LimsHeader from "./components/LimsHeader.vue";
import LimsTools from "./components/LimsTools.vue";
import UserMenu from "./components/UserMenu.vue";

const route = useRoute();
const router = useRouter();
const collapsed = ref(false);

const items = [
	{ label: "仪表盘", to: "/lims/dashboard", icon: LayoutDashboard },
	{ label: "检测请求", to: "/lims/requests", icon: ClipboardList },
	{ label: "试验计划", to: "/lims/plans", icon: CalendarClock },
	{ label: "检测报告", to: "/lims/reports", icon: FileText },
	{ label: "客户", to: "/lims/customers", icon: Users },
	{ label: "测试标准", to: "/lims/standards", icon: BookOpen },
	{ label: "检测项目", to: "/lims/items", icon: Package },
	{ label: "设备(Asset)", to: "/lims/assets", icon: Wrench },
	{ label: "协议价", to: "/lims/catalog", icon: FolderKanban },
];

const active = computed(() => route.path);

function isActive(to) {
	return active.value.startsWith(to);
}
</script>
