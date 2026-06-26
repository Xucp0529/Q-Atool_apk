#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q&A 答题工具 — Flask Web 应用
用于 python-for-android WebView bootstrap 打包为 APK
"""

import os
import random
from flask import Flask, render_template, request, jsonify

import qa_core

app = Flask(__name__)
app.secret_key = "qa_tool_secret_2024"

# -------------------- 全局游戏状态 --------------------
# 单用户本地应用，用全局状态即可

class GameState:
    def __init__(self):
        self.qa_pairs = []
        self.forgotten_set = set()
        self.current_index = 0
        self.question_count = 0
        self.current_pair = None
        self.qa_file = qa_core.DEFAULT_QA_FILE
        self.forget_path = ""
        self.mode = "idle"  # "answering" | "ungd_result" | "gd_result"

    def load_qa_file(self, qa_file=None):
        if qa_file is None:
            qa_file = self.qa_file
        self.qa_file = qa_file

        qa_path = os.path.join(qa_core.get_txt_dir(), qa_file)
        forget_filename = qa_core.get_forget_filename(qa_file)
        self.forget_path = os.path.join(qa_core.get_txt_dir(), forget_filename)

        self.qa_pairs = qa_core.load_qa_pairs(qa_path)
        self.forgotten_set = qa_core.load_forgotten_questions(self.forget_path)

        if self.qa_pairs:
            random.shuffle(self.qa_pairs)
        self.current_index = 0
        self.question_count = 0
        self.current_pair = None
        self.mode = "idle"

    def get_next_question(self):
        if not self.qa_pairs:
            return None

        # 每 SHUFFLE_INTERVAL 题打乱
        if self.question_count > 0 and self.question_count % qa_core.SHUFFLE_INTERVAL == 0:
            random.shuffle(self.qa_pairs)
            self.current_index = 0

        if self.current_index >= len(self.qa_pairs):
            random.shuffle(self.qa_pairs)
            self.current_index = 0

        self.current_pair = self.qa_pairs[self.current_index]
        self.current_index += 1
        self.question_count += 1
        self.mode = "answering"

        return {
            "identifier": self.current_pair[0],
            "question": self.current_pair[1],
            "progress": f"第 {self.question_count} 题 | 题库共 {len(self.qa_pairs)} 题",
            "total": len(self.qa_pairs),
            "current": self.question_count,
        }

    def check_gd_answer(self, user_answer):
        """gd模式：逐字对比答案"""
        if not self.current_pair:
            return None
        _, question, correct_answer = self.current_pair
        user_answer = user_answer.strip()
        if not user_answer:
            user_answer = "(空)"

        is_wrong = (user_answer != correct_answer)
        correct_parts, your_parts = qa_core.compare_char_by_char(user_answer, correct_answer)

        # 错误自动存入遗忘题库
        status = ""
        if is_wrong:
            if question in self.forgotten_set:
                status = "答案有出入（该题已在遗忘题库中）"
            else:
                qa_core.save_forgotten_question(
                    self.forget_path,
                    self.current_pair[0],
                    question,
                    correct_answer
                )
                self.forgotten_set.add(question)
                status = "答案有出入，已自动存入遗忘题库"
        else:
            status = "答案完全正确 ✓"

        self.mode = "gd_result"

        return {
            "correct_parts": correct_parts,
            "your_parts": your_parts,
            "status": status,
            "correct_answer": correct_answer,
        }

    def get_ungd_answer(self):
        """ungd模式：显示标准答案"""
        if not self.current_pair:
            return None
        self.mode = "ungd_result"
        return {
            "answer": self.current_pair[2],
        }

    def mark_forgotten(self):
        """标记为遗忘"""
        if not self.current_pair:
            return
        identifier, question, answer = self.current_pair
        if question not in self.forgotten_set:
            qa_core.save_forgotten_question(self.forget_path, identifier, question, answer)
            self.forgotten_set.add(question)
            return "已存入遗忘题库"
        return "该题已在遗忘题库中"

    def mark_remembered(self):
        """标记为记得"""
        return "已标记：记得"

    def to_dict(self):
        return {
            "mode": self.mode,
            "qa_file": self.qa_file,
            "total": len(self.qa_pairs),
            "current": self.question_count,
            "progress": f"第 {self.question_count} 题 | 题库共 {len(self.qa_pairs)} 题",
        }


# 全局状态实例
state = GameState()

# 启动时加载设置中的题库
settings = qa_core.load_app_settings()
state.load_qa_file(settings.get("qa_file", qa_core.DEFAULT_QA_FILE))


# -------------------- 页面路由 --------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


# -------------------- API 路由 --------------------

@app.route("/api/state")
def get_state():
    """获取当前状态"""
    d = state.to_dict()
    if state.current_pair:
        d["identifier"] = state.current_pair[0]
        d["question"] = state.current_pair[1]
    return jsonify(d)


@app.route("/api/start", methods=["POST"])
def start_quiz():
    """开始/重启答题"""
    data = request.get_json() or {}
    qa_file = data.get("qa_file")
    state.load_qa_file(qa_file)
    result = state.get_next_question()
    if result is None:
        return jsonify({"error": "题库为空"}), 400
    return jsonify(result)


@app.route("/api/next", methods=["POST"])
def next_question():
    """获取下一题"""
    result = state.get_next_question()
    if result is None:
        return jsonify({"error": "题库为空"}), 400
    return jsonify(result)


@app.route("/api/check", methods=["POST"])
def check_answer():
    """检查答案（gd模式）或显示答案（ungd模式）"""
    if not state.current_pair:
        return jsonify({"error": "没有当前题目"}), 400

    identifier = state.current_pair[0]

    if identifier == "gd":
        data = request.get_json() or {}
        user_answer = data.get("answer", "")
        result = state.check_gd_answer(user_answer)
        if result is None:
            return jsonify({"error": "检查答案失败"}), 400
        return jsonify({"type": "gd", **result})
    else:
        result = state.get_ungd_answer()
        if result is None:
            return jsonify({"error": "获取答案失败"}), 400
        return jsonify({"type": "ungd", **result})


@app.route("/api/remember", methods=["POST"])
def remember():
    """ungd模式：标记为记得"""
    msg = state.mark_remembered()
    return jsonify({"status": msg})


@app.route("/api/forget", methods=["POST"])
def forget():
    """标记为遗忘（ungd模式按钮 或 手动遗忘）"""
    msg = state.mark_forgotten()
    return jsonify({"status": msg})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """获取设置"""
    s = qa_core.load_app_settings()
    files = qa_core.get_available_txt_files()
    return jsonify({
        "qa_file": s.get("qa_file", qa_core.DEFAULT_QA_FILE),
        "available_files": files,
    })


@app.route("/api/settings", methods=["POST"])
def save_settings():
    """保存设置"""
    data = request.get_json() or {}
    qa_file = data.get("qa_file", qa_core.DEFAULT_QA_FILE)
    qa_core.save_app_settings({"qa_file": qa_file})
    state.load_qa_file(qa_file)
    return jsonify({"status": "设置已保存", "qa_file": qa_file})


@app.route("/api/clear_forgotten", methods=["POST"])
def clear_forgotten():
    """清空遗忘题库"""
    qa_core.clear_forgotten_file(state.forget_path)
    state.forgotten_set.clear()
    return jsonify({"status": "遗忘记录已清除"})


# -------------------- 入口 --------------------

if __name__ == "__main__":
    print("Q&A 答题工具服务器启动...")
    print("在浏览器中打开 http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
