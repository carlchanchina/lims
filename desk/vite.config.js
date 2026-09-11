import path from "node:path";
import { fileURLToPath } from "node:url";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { defineConfig } from "vite";
import frappeUI from "frappe-ui/vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function limsBootTemplate() {
	return {
		name: "lims-boot-template",
		transformIndexHtml(html, context) {
			if (context.server) return html;
			return html.replace(
				"</body>",
				`<script>window.__boot = {% if lims_boot %}{{ lims_boot | safe }}{% else %}null{% endif %};</script>\n</body>`
			);
		},
	};
}

export default defineConfig({
	plugins: [
		frappeUI({
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: false,
			buildConfig: {
				outDir: "../lims/public/lims",
				emptyOutDir: true,
				indexHtmlPath: "../lims/www/lims/index.html",
			},
		}),
		vue(),
		vueJsx(),
		limsBootTemplate(),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
		dedupe: ["vue", "vue-router", "frappe-ui", "reka-ui"],
	},
	server: {
		allowedHosts: true,
		fs: {
			allow: [".."],
		},
	},
});
