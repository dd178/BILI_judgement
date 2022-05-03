#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022-05-03 20:29:29
# @Author  : Qiuyelin
# @File    : log.py
# @Software: PyCharm

import logging.config
import sys

def outputLog():
    log = logging.getLogger('BILI_judgement')
    log.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s]\t%(message)s')
    # 输出日志到终端
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter
    log.addHandler(console_handler)
    #输出日志到文件
    file_handler = logging.FileHandler('BILI_judgement.log')
    file_handler.formatter = formatter
    file_handler.level = logging.INFO
    log.addHandler(file_handler)
    return log
