<template>
	<Dropdown :options="options">
		<template #default="{ open }">
			<button
				class="flex h-12 w-full items-center rounded-md px-2 py-2 duration-300 ease-in-out"
				:class="open ? 'bg-surface-base shadow-sm' : 'hover:bg-surface-gray-3'"
			>
				<div
					class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-gray-7 text-base font-semibold text-white"
				>
					L
				</div>
				<div
					v-if="!collapsed"
					class="ms-2 flex min-w-0 flex-1 flex-col text-start"
				>
					<div class="truncate text-base-medium leading-none text-ink-gray-9">
						环境试验 LIMS
					</div>
					<div class="mt-1 truncate text-sm text-ink-gray-7">{{ user }}</div>
				</div>
				<FeatherIcon
					v-if="!collapsed"
					name="chevron-down"
					class="ms-2 size-4 shrink-0 text-ink-gray-5"
				/>
			</button>
		</template>
	</Dropdown>
</template>

<script setup>
import { Dropdown, FeatherIcon, useTheme } from "frappe-ui";
import { computed } from "vue";
import { getBoot } from "../boot";

defineProps({ collapsed: { type: Boolean, default: false } });

const boot = getBoot();
const user = computed(() => boot.session_user);
const { currentTheme, toggleTheme } = useTheme();

const options = computed(() => [
	{
		label: "打开 Frappe Desk",
		icon: "lucide-layout-dashboard",
		onClick: () => (window.location.href = "/app"),
	},
	{
		label: currentTheme.value === "dark" ? "切换浅色模式" : "切换深色模式",
		icon: "lucide-sun-moon",
		onClick: () => toggleTheme(),
	},
	{
		label: "退出登录",
		icon: "lucide-log-out",
		onClick: () => (window.location.href = "/api/method/logout"),
	},
]);
</script>
