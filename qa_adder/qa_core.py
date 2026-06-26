#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA 添加器 — 业务逻辑模块
- 题库文件管理（新增/移除）
- 题目追加
- 配置文件读写
"""

import os
import sys
import json

# -------------------- 常量 --------------------
CONFIG_FILENAME = "qa_config.json"
TXT_DIR = "Q&A_txt"

BUILTIN_QA_FILES = {
    "qa.txt": "默认题库",
}


# -------------------- 路径工具 --------------------

def get_app_dir():
    """获取应用所在目录（兼容 PyInstaller 打包 和 Android p4a）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_txt_dir():
    """获取题库文件子目录路径，若不存在则自动创建"""
    d = os.path.join(get_app_dir(), TXT_DIR)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def get_config_path():
    """获取配置文件路径"""
    return os.path.join(get_app_dir(), CONFIG_FILENAME)


# -------------------- 题库管理 --------------------

def load_qa_files():
    """加载题库字典：内置默认 + 配置文件中的自定义题库"""
    qa_files = dict(BUILTIN_QA_FILES)

    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                custom = json.load(f)
            if isinstance(custom, dict):
                qa_files.update(custom)
        except (json.JSONDecodeError, IOError):
            pass

    # 过滤被排除的内置题库
    excluded = _get_excluded_builtins()
    for key in excluded:
        if key in qa_files:
            del qa_files[key]

    return qa_files


def _get_excluded_builtins():
    """获取被排除的内置题库列表"""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if isinstance(config, dict):
            excluded = config.get("_excluded_builtins", [])
            return excluded if isinstance(excluded, list) else []
    except (json.JSONDecodeError, IOError):
        pass
    return []


def save_custom_qa_files(custom_qa_files):
    """将自定义题库字典写入配置文件（保留排除列表）"""
    config_path = get_config_path()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    if not isinstance(config, dict):
        config = {}

    # 保留 _excluded_builtins
    excluded = config.get("_excluded_builtins", [])
    config = {"_excluded_builtins": excluded}
    config.update(custom_qa_files)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_custom_qa_files():
    """获取仅自定义的题库"""
    all_files = load_qa_files()
    return {k: v for k, v in all_files.items() if k not in BUILTIN_QA_FILES}


def remove_qa_file(filename):
    """从列表中移除题库文件（内置→排除列表，自定义→删除配置）"""
    if filename in BUILTIN_QA_FILES:
        _exclude_builtin(filename)
    else:
        custom = get_custom_qa_files()
        if filename in custom:
            del custom[filename]
            save_custom_qa_files(custom)


def _exclude_builtin(filename):
    """将内置题库加入排除列表"""
    config_path = get_config_path()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    if not isinstance(config, dict):
        config = {}

    excluded = config.get("_excluded_builtins", [])
    if not isinstance(excluded, list):
        excluded = []
    if filename not in excluded:
        excluded.append(filename)
    config["_excluded_builtins"] = excluded

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# -------------------- 题目追加 --------------------

def append_qa(filename, identifier, question, answer):
    """将题目追加到指定题库文件"""
    qa_path = os.path.join(get_txt_dir(), filename)
    with open(qa_path, "a", encoding="utf-8") as f:
        f.write(f"{identifier}\n/\n{question}\n/\n{answer}\n//\n")


def create_empty_qa_file(filename):
    """创建空的题库文件"""
    file_path = os.path.join(get_txt_dir(), filename)
    with open(file_path, "w", encoding="utf-8"):
        pass


def validate_filename(filename):
    """验证文件名是否合法，返回 (is_valid, error_message)"""
    if not filename:
        return False, "文件名不能为空"
    if "/" in filename or "\\" in filename:
        return False, "文件名不能包含路径分隔符"
    if not filename.endswith(".txt"):
        return False, "文件名必须以 .txt 结尾"
    return True, ""
