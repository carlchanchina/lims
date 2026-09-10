<template>
	<SidebarItem :label="__('搜索')" @click="search?.openSearch()">
		<template #prefix>
			<component :is="SearchIcon" class="size-4" />
		</template>
		<template #suffix>
			<span class="me-2 text-xs text-ink-gray-5">⌘K</span>
		</template>
	</SidebarItem>
	<SidebarItem
		id="notifications-btn"
		:label="__('通知')"
		@click="notifications?.toggle()"
	>
		<template #prefix>
			<component :is="BellIcon" class="size-4" />
		</template>
		<template #suffix>
			<Badge v-if="unread" theme="gray" variant="subtle" :label="unread > 9 ? '9+' : unread" />
		</template>
	</SidebarItem>
	<GlobalSearch ref="search" />
	<NotificationsPanel
		ref="notifications"
		:collapsed="collapsed"
		@unread="unread = $event"
	/>
</template>

<script setup>
import { Badge, SidebarItem } from "frappe-ui";
import { ref } from "vue";
import BellIcon from "~icons/lucide/bell";
import SearchIcon from "~icons/lucide/search";
import GlobalSearch from "./GlobalSearch.vue";
import NotificationsPanel from "./NotificationsPanel.vue";

defineProps({ collapsed: { type: Boolean, default: false } });
const __ = (text) => text;

const search = ref(null);
const notifications = ref(null);
const unread = ref(0);
</script>
