import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import frappeUI from "frappe-ui/vite";

export default defineConfig({
	plugins: [
		frappeUI({
			frappeProxy: true,
			lucideIcons: true,
			buildConfig: {
				outDir: "../test/public/lims",
				emptyOutDir: true,
				indexHtmlPath: "../test/www/lims/index.html",
			},
		}),
		vue(),
	],
	server: {
		port: 5173,
	},
});
