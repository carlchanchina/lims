# 环境试验 LIMS Vue 前端

技术栈:Vue 3 + Vite + Vue Router + frappe-ui + Tailwind。

构建产物写入 `../test/public/lims`,页面模板写入 `../test/www/lims/index.html`,站点访问地址为 `/lims`。

## Development

需要在完整 bench(含 Frappe + ERPNext)中运行:

```bash
cd desk
yarn install
yarn dev
```

Vite `frappeProxy` 会把 `/api`、`/assets` 代理到本地 Frappe 站点;若站点地址不是
`http://localhost:8000`,按 frappe-ui/vite 约定配置代理地址。

## Production build

```bash
cd desk
yarn install
yarn build
```

构建完成后在站点执行 `bench --site <site> migrate`(如需清缓存再执行
`bench --site <site> clear-cache`)并访问 `https://<site>/lims`。

## 页面

- `/lims/dashboard` 仪表盘
- `/lims/requests` 检测请求列表
- `/lims/requests/:name` 请求详情(样品/测试项/报价/状态)
- `/lims/reports` 检测报告
- `/lims/standards`、`/lims/equipment`、`/lims/catalog` 主数据
