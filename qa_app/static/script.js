/* ============================================================
   Q&A 答题工具 — 前端逻辑
   ============================================================ */

// ---------- DOM 引用 ----------
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// 页面元素
const questionCard = $("#question-card");
const questionText = $("#question-text");
const progressChip = $("#progress-chip");
const statusBar = $("#status-bar");

// 模式区域
const answeringSection = $("#answering-section");
const ungdResultSection = $("#ungd-result-section");
const gdResultSection = $("#gd-result-section");

// 输入区
const answerInput = $("#answer-input");
const submitBtn = $("#submit-btn");
const nextBtn1 = $("#next-btn-1");
const nextBtn2 = $("#next-btn-2");

// ungd 按钮
const rememberBtn = $("#remember-btn");
const forgetBtn = $("#forget-btn");

// 答案显示区
const ungdAnswer = $("#ungd-answer");
const yourAnswerDisplay = $("#your-answer-display");
const correctAnswerDisplay = $("#correct-answer-display");

// Top bar
const settingsBtn = $("#settings-btn");
const clearForgottenBtn = $("#clear-forgotten-btn");

// Modal
const modalOverlay = $("#modal-overlay");
const modalCancel = $("#modal-cancel");
const modalConfirm = $("#modal-confirm");
const modalMessage = $("#modal-message");

// Toast
const toast = $("#toast");

// ---------- 状态 ----------
let currentMode = ""; // "ungd" | "gd"

// ---------- 初始化 ----------
document.addEventListener("DOMContentLoaded", () => {
  loadState();
});

async function loadState() {
  try {
    const resp = await fetch("/api/state");
    const data = await resp.json();

    if (data.mode === "idle" || data.question === undefined) {
      // 首次加载，开始新答题
      startQuiz();
    } else {
      // 恢复状态（理论上不常见，但做兼容）
      updateProgress(data.current, data.total);
      if (data.question) {
        showQuestion(data.identifier, data.question, data.current, data.total);
      }
    }
  } catch (e) {
    // 服务器可能还没就绪，等一会再试
    setTimeout(loadState, 500);
  }
}

async function startQuiz() {
  try {
    const resp = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await resp.json();
    if (data.error) {
      showToast(data.error, true);
      showEmptyState(data.error);
      return;
    }
    showQuestion(data.identifier, data.question, data.current, data.total);
  } catch (e) {
    showToast("连接服务器失败", true);
  }
}

// ---------- 显示题目 ----------
function showQuestion(identifier, question, current, total) {
  currentMode = identifier === "gd" ? "gd" : "ungd";

  // 显示题目
  questionCard.classList.remove("hidden");
  questionText.textContent = question;
  updateProgress(current, total);

  // 切换到答题模式
  answeringSection.classList.remove("hidden");
  ungdResultSection.classList.add("hidden");
  gdResultSection.classList.add("hidden");

  // 重置输入
  answerInput.value = "";
  answerInput.disabled = false;
  answerInput.focus();
  submitBtn.classList.remove("hidden");
  nextBtn1.classList.add("hidden");
  nextBtn2.classList.add("hidden");

  statusBar.textContent = "";
  statusBar.className = "status-bar";

  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateProgress(current, total) {
  if (total > 0) {
    progressChip.textContent = `📝 第 ${current} / ${total} 题`;
  } else {
    progressChip.textContent = "题库为空";
  }
}

// ---------- 提交答案 ----------
submitBtn.addEventListener("click", submitAnswer);
answerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitAnswer();
});

async function submitAnswer() {
  const answer = answerInput.value;

  submitBtn.disabled = true;

  try {
    const resp = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    const data = await resp.json();

    if (data.error) {
      showToast(data.error, true);
      submitBtn.disabled = false;
      return;
    }

    answeringSection.classList.add("hidden");
    answerInput.disabled = true;
    submitBtn.classList.add("hidden");

    if (data.type === "gd") {
      // gd 模式：显示对比结果
      showGdResult(data);
    } else {
      // ungd 模式：显示标准答案
      showUngdResult(data);
    }
  } catch (e) {
    showToast("提交失败，请重试", true);
    submitBtn.disabled = false;
  }
}

// ---------- ungd 模式结果 ----------
function showUngdResult(data) {
  ungdResultSection.classList.remove("hidden");
  ungdAnswer.textContent = data.answer;

  rememberBtn.disabled = false;
  forgetBtn.disabled = false;
  nextBtn1.classList.add("hidden");

  statusBar.textContent = "请判断是否记住了这道题";
  statusBar.className = "status-bar";
}

rememberBtn.addEventListener("click", async () => {
  rememberBtn.disabled = true;
  forgetBtn.disabled = true;

  await fetch("/api/remember", { method: "POST" });
  statusBar.textContent = "已标记：记得 ✓";
  statusBar.className = "status-bar success";

  nextBtn1.classList.remove("hidden");
  nextBtn1.focus();
});

forgetBtn.addEventListener("click", async () => {
  rememberBtn.disabled = true;
  forgetBtn.disabled = true;

  const resp = await fetch("/api/forget", { method: "POST" });
  const data = await resp.json();
  statusBar.textContent = data.status;
  statusBar.className = "status-bar warning";

  nextBtn1.classList.remove("hidden");
  nextBtn1.focus();
});

// ---------- gd 模式结果 ----------
function showGdResult(data) {
  gdResultSection.classList.remove("hidden");

  // 用户答案（高亮差异）
  yourAnswerDisplay.innerHTML = "";
  if (data.your_parts && data.your_parts.length > 0) {
    data.your_parts.forEach(([char, isDiff]) => {
      const span = document.createElement("span");
      span.textContent = char;
      if (isDiff) span.className = "char-diff";
      else span.className = "char-match";
      yourAnswerDisplay.appendChild(span);
    });
  } else {
    yourAnswerDisplay.textContent = "(空)";
  }

  // 标准答案（高亮差异）
  correctAnswerDisplay.innerHTML = "";
  if (data.correct_parts && data.correct_parts.length > 0) {
    data.correct_parts.forEach(([char, isDiff]) => {
      const span = document.createElement("span");
      span.textContent = char;
      if (isDiff) span.className = "char-diff";
      else span.className = "char-match";
      correctAnswerDisplay.appendChild(span);
    });
  }

  statusBar.textContent = data.status;
  statusBar.className = data.status.includes("正确") ? "status-bar success" : "status-bar warning";

  nextBtn2.classList.remove("hidden");
  nextBtn2.focus();
}

// ---------- 下一题 ----------
nextBtn1.addEventListener("click", nextQuestion);
nextBtn2.addEventListener("click", nextQuestion);

async function nextQuestion() {
  nextBtn1.disabled = true;
  nextBtn2.disabled = true;

  try {
    const resp = await fetch("/api/next", { method: "POST" });
    const data = await resp.json();

    if (data.error) {
      showToast(data.error, true);
      return;
    }

    showQuestion(data.identifier, data.question, data.current, data.total);
  } catch (e) {
    showToast("获取下一题失败", true);
  }
}

// ---------- 设置按钮 ----------
settingsBtn.addEventListener("click", () => {
  window.location.href = "/settings";
});

// ---------- 清除遗忘 ----------
clearForgottenBtn.addEventListener("click", () => {
  showModal("确定要清除所有遗忘记录吗？此操作不可撤销。", async () => {
    try {
      const resp = await fetch("/api/clear_forgotten", { method: "POST" });
      const data = await resp.json();
      showToast(data.status);
    } catch (e) {
      showToast("操作失败", true);
    }
  });
});

// ---------- Toast ----------
let toastTimer;

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.className = "toast" + (isError ? " error" : "");
  toast.classList.add("show");

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

// ---------- Modal ----------
let modalCallback = null;

function showModal(message, onConfirm) {
  modalMessage.textContent = message;
  modalCallback = onConfirm;
  modalOverlay.classList.remove("hidden");
}

modalCancel.addEventListener("click", hideModal);
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) hideModal();
});

modalConfirm.addEventListener("click", () => {
  if (modalCallback) modalCallback();
  hideModal();
});

function hideModal() {
  modalOverlay.classList.add("hidden");
  modalCallback = null;
}

// ---------- 空状态 ----------
function showEmptyState(message) {
  questionCard.classList.add("hidden");
  answeringSection.classList.add("hidden");
  ungdResultSection.classList.add("hidden");
  gdResultSection.classList.add("hidden");
  statusBar.textContent = message;
}
