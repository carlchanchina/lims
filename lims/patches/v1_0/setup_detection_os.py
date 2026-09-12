# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""一次性迁移:旧角色用户 -> 新角色,并停用旧角色。"""

from lims.setup.detection_os import setup_detection_os


def execute():
	setup_detection_os()
