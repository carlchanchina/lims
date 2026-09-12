# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""初始主数据:环境试验常用的检测标准 / 检测方法 / 检测项目。

只在缺失时创建(不覆盖业务已经改过的记录),用于:
- 新站点安装后立刻能跑通「委托 → 报价 → 报告」;
- 老站点通过 `lims.api.master.seed_starter_masters` 手工补齐。
业务方可以随意增删,脚本只补不删。
"""

STARTER_STANDARDS = (
	{
		"standard_code": "GB/T 2423.1-2008",
		"standard_name": "电工电子产品环境试验 第2部分:试验方法 试验A:低温",
		"version": "2008",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.2-2008",
		"standard_name": "电工电子产品环境试验 第2部分:试验方法 试验B:高温",
		"version": "2008",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.3-2016",
		"standard_name": "环境试验 第2部分:试验方法 试验Cab:恒定湿热试验",
		"version": "2016",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.4-2008",
		"standard_name": "电工电子产品环境试验 第2部分:试验方法 试验Db:交变湿热(12h+12h循环)",
		"version": "2008",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.5-2019",
		"standard_name": "环境试验 第2部分:试验方法 试验Ea和导则:冲击",
		"version": "2019",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.10-2019",
		"standard_name": "环境试验 第2部分:试验方法 试验Fc:振动(正弦)",
		"version": "2019",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GB/T 2423.17-2008",
		"standard_name": "电工电子产品环境试验 第2部分:试验方法 试验Ka:盐雾",
		"version": "2008",
		"organization": "国家标准化管理委员会",
	},
	{
		"standard_code": "GJB 150.3A-2009",
		"standard_name": "军用装备实验室环境试验方法 第3部分:高温试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.4A-2009",
		"standard_name": "军用装备实验室环境试验方法 第4部分:低温试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.5A-2009",
		"standard_name": "军用装备实验室环境试验方法 第5部分:温度冲击试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.9A-2009",
		"standard_name": "军用装备实验室环境试验方法 第9部分:湿热试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.11A-2009",
		"standard_name": "军用装备实验室环境试验方法 第11部分:盐雾试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.16A-2009",
		"standard_name": "军用装备实验室环境试验方法 第16部分:振动试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
	{
		"standard_code": "GJB 150.18A-2009",
		"standard_name": "军用装备实验室环境试验方法 第18部分:冲击试验",
		"version": "2009",
		"organization": "中国人民解放军总装备部",
	},
)

# 每个标准对应一条常用的检测方法(method_code 唯一)
STARTER_METHODS = (
	{"method_code": "M-LOW-TEMP", "method_name": "低温试验方法", "standard_code": "GB/T 2423.1-2008"},
	{"method_code": "M-HIGH-TEMP", "method_name": "高温试验方法", "standard_code": "GB/T 2423.2-2008"},
	{
		"method_code": "M-DAMP-HEAT-STEADY",
		"method_name": "恒定湿热试验方法",
		"standard_code": "GB/T 2423.3-2016",
	},
	{
		"method_code": "M-DAMP-HEAT-CYCLE",
		"method_name": "交变湿热试验方法",
		"standard_code": "GB/T 2423.4-2008",
	},
	{"method_code": "M-SHOCK", "method_name": "冲击试验方法", "standard_code": "GB/T 2423.5-2019"},
	{"method_code": "M-VIBRATION", "method_name": "振动(正弦)试验方法", "standard_code": "GB/T 2423.10-2019"},
	{"method_code": "M-SALT-SPRAY", "method_name": "盐雾试验方法", "standard_code": "GB/T 2423.17-2008"},
	{"method_code": "M-GJB-HIGH-TEMP", "method_name": "高温试验方法(军标)", "standard_code": "GJB 150.3A-2009"},
	{"method_code": "M-GJB-LOW-TEMP", "method_name": "低温试验方法(军标)", "standard_code": "GJB 150.4A-2009"},
	{
		"method_code": "M-GJB-THERMAL-SHOCK",
		"method_name": "温度冲击试验方法(军标)",
		"standard_code": "GJB 150.5A-2009",
	},
	{"method_code": "M-GJB-DAMP-HEAT", "method_name": "湿热试验方法(军标)", "standard_code": "GJB 150.9A-2009"},
	{"method_code": "M-GJB-SALT-SPRAY", "method_name": "盐雾试验方法(军标)", "standard_code": "GJB 150.11A-2009"},
	{"method_code": "M-GJB-VIBRATION", "method_name": "振动试验方法(军标)", "standard_code": "GJB 150.16A-2009"},
	{"method_code": "M-GJB-SHOCK", "method_name": "冲击试验方法(军标)", "standard_code": "GJB 150.18A-2009"},
)

# ERPNext Item:检测项目按服务型销售物料建
STARTER_TEST_ITEMS = (
	{"item_code": "TEST-LOW-TEMP", "item_name": "低温试验"},
	{"item_code": "TEST-HIGH-TEMP", "item_name": "高温试验"},
	{"item_code": "TEST-DAMP-HEAT", "item_name": "湿热试验"},
	{"item_code": "TEST-THERMAL-SHOCK", "item_name": "温度冲击试验"},
	{"item_code": "TEST-TEMP-CYCLE", "item_name": "温度循环试验"},
	{"item_code": "TEST-VIBRATION", "item_name": "振动试验"},
	{"item_code": "TEST-SHOCK", "item_name": "冲击试验"},
	{"item_code": "TEST-SALT-SPRAY", "item_name": "盐雾试验"},
)
