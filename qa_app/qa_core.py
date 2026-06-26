#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q&A 工具 — 共享业务逻辑模块
- 题库文件加载/解析
- 答案逐字对比
- 遗忘题目管理
- 设置管理
- 文件/路径工具
"""

import os
import sys
import json

# -------------------- 常量 --------------------
DEFAULT_QA_FILE = "qa.txt"
FORGET_FILE = "qa_forget.txt"
SHUFFLE_INTERVAL = 20
SETTINGS_FILE = "qa_settings.json"
TXT_DIR = "Q&A_txt"


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


def get_available_txt_files():
    """获取 Q&A_txt 目录下所有 .txt 文件"""
    txt_dir = get_txt_dir()
    txt_files = []
    try:
        for fname in os.listdir(txt_dir):
            if fname.endswith(".txt") and os.path.isfile(os.path.join(txt_dir, fname)):
                txt_files.append(fname)
    except OSError:
        pass
    return sorted(txt_files)


def get_forget_filename(qa_filename):
    """从题库文件名推导遗忘文件名"""
    if qa_filename == DEFAULT_QA_FILE:
        return FORGET_FILE
    return qa_filename.replace(".txt", "-forget.txt")


# -------------------- 题目加载 --------------------

def load_qa_pairs(filepath):
    """读取题库文件，返回 [(identifier, question, answer), ...] 列表
    格式：识别符 / 问题 / 答案 //
    """
    pairs = []
    if not os.path.exists(filepath):
        return pairs

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    id_lines = []
    q_lines = []
    a_lines = []
    current = "identifier"

    for line in lines:
        s = line.strip()
        if s == "//":
            if id_lines or q_lines or a_lines:
                ident = "\n".join(id_lines).strip()
                question = "\n".join(q_lines).strip()
                answer = "\n".join(a_lines).strip()
                if ident and (question or answer):
                    pairs.append((ident, question, answer))
            id_lines, q_lines, a_lines = [], [], []
            current = "identifier"
        elif s == "/":
            if current == "identifier":
                current = "question"
            elif current == "question":
                current = "answer"
        else:
            if current == "identifier":
                id_lines.append(s)
            elif current == "question":
                q_lines.append(s)
            else:
                a_lines.append(s)

    if id_lines or q_lines or a_lines:
        ident = "\n".join(id_lines).strip()
        question = "\n".join(q_lines).strip()
        answer = "\n".join(a_lines).strip()
        if ident and (question or answer):
            pairs.append((ident, question, answer))

    return pairs


def load_forgotten_questions(filepath):
    """读取已遗忘题库，返回问题文本集合（用于去重）"""
    forgotten = set()
    if not os.path.exists(filepath):
        return forgotten

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    q_lines = []
    current = "identifier"

    for line in lines:
        s = line.strip()
        if s == "//":
            if q_lines:
                forgotten.add("\n".join(q_lines).strip())
            q_lines = []
            current = "identifier"
        elif s == "/":
            if current == "identifier":
                current = "question"
            elif current == "question":
                current = "answer"
        else:
            if current == "question":
                q_lines.append(s)

    if q_lines:
        forgotten.add("\n".join(q_lines).strip())

    return forgotten


def save_forgotten_question(filepath, identifier, question, answer):
    """将遗忘的题目追加到遗忘题库文件"""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{identifier}\n/\n{question}\n/\n{answer}\n//\n")


# -------------------- 答案对比 --------------------

def compare_char_by_char(typed, correct):
    """逐字对比，返回 (correct_parts, your_parts)
    每项为 [[char, is_diff], ...] 列表
    """
    max_len = max(len(typed), len(correct))
    correct_parts = []
    your_parts = []

    for i in range(max_len):
        tc = typed[i] if i < len(typed) else ""
        cc = correct[i] if i < len(correct) else ""
        is_diff = tc != cc

        if i < len(correct):
            correct_parts.append([cc, is_diff])
        if i < len(typed):
            your_parts.append([tc, is_diff])

    return correct_parts, your_parts


# -------------------- 设置管理 --------------------

def load_app_settings():
    """加载应用设置，返回 {qa_file}"""
    default = {"qa_file": DEFAULT_QA_FILE}
    settings_path = os.path.join(get_app_dir(), SETTINGS_FILE)
    if not os.path.exists(settings_path):
        return default
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "qa_file" in data:
                default["qa_file"] = data["qa_file"]
            elif "random_qa_file" in data:
                default["qa_file"] = data["random_qa_file"]
        return default
    except (json.JSONDecodeError, IOError):
        return default


def save_app_settings(settings):
    """保存应用设置"""
    settings_path = os.path.join(get_app_dir(), SETTINGS_FILE)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def clear_forgotten_file(forget_path):
    """清空遗忘题库文件"""
    with open(forget_path, "w", encoding="utf-8") as f:
        f.write("")
