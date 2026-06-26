#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA 添加器 — Flask Web 应用
用于 python-for-android WebView bootstrap 打包为 APK
"""

import os
from flask import Flask, render_template, request, jsonify

import qa_core

app = Flask(__name__)
app.secret_key = "qa_adder_secret_2024"


# -------------------- 页面路由 --------------------

@app.route("/")
def index():
    return render_template("index.html")


# -------------------- API 路由 --------------------

@app.route("/api/files", methods=["GET"])
def get_files():
    """获取可用题库文件列表"""
    qa_files = qa_core.load_qa_files()
    files = []
    for filename, desc in qa_files.items():
        files.append({"filename": filename, "description": desc})
    return jsonify({"files": files})


@app.route("/api/add", methods=["POST"])
def add_question():
    """添加题目到指定题库"""
    data = request.get_json() or {}
    target_file = data.get("file", "").strip()
    identifier = data.get("type", "ungd").strip()
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()

    # 验证
    if not target_file:
        return jsonify({"error": "请选择题库文件"}), 400
    if not question:
        return jsonify({"error": "问题不能为空"}), 400
    if not answer:
        return jsonify({"error": "答案不能为空"}), 400
    if identifier not in ("ungd", "gd"):
        return jsonify({"error": "题型必须是 ungd 或 gd"}), 400

    # 验证文件存在
    qa_files = qa_core.load_qa_files()
    if target_file not in qa_files:
        return jsonify({"error": f"题库「{target_file}」不存在"}), 400

    # 追加题目
    try:
        qa_core.append_qa(target_file, identifier, question, answer)
    except IOError as e:
        return jsonify({"error": f"写入文件失败：{e}"}), 500

    return jsonify({"status": "题目已添加成功！"})


@app.route("/api/new_file", methods=["POST"])
def new_file():
    """创建新题库文件"""
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()
    description = data.get("description", "").strip()

    # 验证文件名
    is_valid, err_msg = qa_core.validate_filename(filename)
    if not is_valid:
        return jsonify({"error": err_msg}), 400

    # 检查是否重名
    existing = qa_core.load_qa_files()
    if filename in existing:
        return jsonify({"error": f"题库「{filename}」已存在"}), 400

    # 创建文件
    try:
        qa_core.create_empty_qa_file(filename)
    except IOError as e:
        return jsonify({"error": f"无法创建文件：{e}"}), 500

    # 保存到配置
    custom = qa_core.get_custom_qa_files()
    custom[filename] = description or filename
    qa_core.save_custom_qa_files(custom)

    return jsonify({"status": f"题库「{filename}」已添加！", "filename": filename})


@app.route("/api/remove_file", methods=["POST"])
def remove_file():
    """从列表中移除题库文件（不删除物理文件）"""
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()

    if not filename:
        return jsonify({"error": "请指定要移除的文件"}), 400

    # 不允许移除最后一个题库
    qa_files = qa_core.load_qa_files()
    if filename not in qa_files:
        return jsonify({"error": f"题库「{filename}」不在列表中"}), 400
    if len(qa_files) <= 1:
        return jsonify({"error": "至少保留一个题库"}), 400

    qa_core.remove_qa_file(filename)

    return jsonify({"status": f"题库「{filename}」已从列表中移除"})


# -------------------- 入口 --------------------

if __name__ == "__main__":
    print("QA 添加器服务器启动...")
    print("在浏览器中打开 http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
