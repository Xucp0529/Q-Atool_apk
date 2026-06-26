/* ============================================================
   QA 添加器 — 前端逻辑
   ============================================================ */

const $ = (sel) => document.querySelector(sel);

// DOM 引用
const fileSelect = $("#file-select");
const fileDescription = $("#file-description");
const typeUngd = $("#type-ungd");
const typeGd = $("#type-gd");
const questionInput = $("#question-input");
const answerInput = $("#answer-input");
const addBtn = $("#add-btn");
const newFileBtn = $("#new-file-btn");
const removeFileBtn = $("#remove-file-btn");
const statusBar = $("#status-bar");
const toast = $("#toast");

// Modal
const modalOverlay = $("#modal-overlay");
const modalTitle = $("#modal-title");
const modalFilename = $("#modal-filename");
const modalDesc = $("#modal-description");
const modalConfirm = $("#modal-confirm");
const modalCancel = $("#modal-cancel");

// Remove modal
const removeModalOverlay = $("#remove-modal-overlay");
const removeModalMessage = $("#remove-modal-message");
const removeModalConfirm = $("#remove-modal-confirm");
const removeModalCancel = $("#remove-modal-cancel");

// ---------- 初始化 ----------
document.addEventListener("DOMContentLoaded", loadFiles);

async function loadFiles() {
  try {
    const resp = await fetch("/api/files");
    const data = await resp.json();

    fileSelect.innerHTML = "";
    if (data.files.length === 0) {
      fileSelect.innerHTML = '<option value="">无可用题库</option>';
      return;
    }

    data.files.forEach((f, i) => {
      const opt = document.createElement("option");
      opt.value = f.filename;
      opt.textContent = `${f.filename} — ${f.description}`;
      if (i === 0) opt.selected = true;
      fileSelect.appendChild(opt);
    });

    updateDescription();
  } catch (e) {
    showToast("加载题库失败", true);
  }
}

fileSelect.addEventListener("change", updateDescription);

function updateDescription() {
  const selected = fileSelect.selectedOptions[0];
  if (selected) {
    fileDescription.textContent = `当前：${selected.textContent}`;
  }
}

// ---------- 添加题目 ----------
addBtn.addEventListener("click", addQuestion);

// Ctrl+Enter 快捷添加
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    addQuestion();
  }
});

async function addQuestion() {
  const file = fileSelect.value;
  const type = typeUngd.checked ? "ungd" : "gd";
  const question = questionInput.value.trim();
  const answer = answerInput.value.trim();

  if (!file) {
    showToast("请选择题库文件", true);
    return;
  }
  if (!question) {
    showToast("问题不能为空", true);
    questionInput.focus();
    return;
  }
  if (!answer) {
    showToast("答案不能为空", true);
    answerInput.focus();
    return;
  }

  addBtn.disabled = true;
  addBtn.textContent = "添加中...";

  try {
    const resp = await fetch("/api/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file, type, question, answer }),
    });
    const data = await resp.json();

    if (data.error) {
      showToast(data.error, true);
    } else {
      showToast(data.status);
      statusBar.textContent = data.status;
      statusBar.className = "status-bar success";

      // 清空输入框
      questionInput.value = "";
      answerInput.value = "";
      questionInput.focus();
    }
  } catch (e) {
    showToast("添加失败，请重试", true);
  }

  addBtn.disabled = false;
  addBtn.textContent = "添加题目";
}

// ---------- 新增题库 ----------
newFileBtn.addEventListener("click", () => {
  modalTitle.textContent = "新增题库";
  modalFilename.value = "";
  modalDesc.value = "";
  modalOverlay.classList.remove("hidden");
  modalFilename.focus();
});

modalCancel.addEventListener("click", () => {
  modalOverlay.classList.add("hidden");
});

modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) modalOverlay.classList.add("hidden");
});

modalConfirm.addEventListener("click", async () => {
  const filename = modalFilename.value.trim();
  const description = modalDesc.value.trim();

  if (!filename) {
    showToast("请输入文件名", true);
    return;
  }
  if (!filename.endsWith(".txt")) {
    showToast("文件名必须以 .txt 结尾", true);
    return;
  }

  modalConfirm.disabled = true;

  try {
    const resp = await fetch("/api/new_file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, description }),
    });
    const data = await resp.json();

    if (data.error) {
      showToast(data.error, true);
    } else {
      showToast(data.status);
      modalOverlay.classList.add("hidden");
      await loadFiles();
      // 选中新文件
      for (let i = 0; i < fileSelect.options.length; i++) {
        if (fileSelect.options[i].value === filename) {
          fileSelect.selectedIndex = i;
          break;
        }
      }
      updateDescription();
    }
  } catch (e) {
    showToast("创建失败", true);
  }

  modalConfirm.disabled = false;
});

// ---------- 移除题库 ----------
removeFileBtn.addEventListener("click", () => {
  const file = fileSelect.value;
  if (!file) {
    showToast("请先选择题库", true);
    return;
  }
  removeModalMessage.textContent = `确定要将题库「${file}」从列表中移除吗？题库文件本身不会被删除。`;
  removeModalOverlay.classList.remove("hidden");
});

removeModalCancel.addEventListener("click", () => {
  removeModalOverlay.classList.add("hidden");
});

removeModalOverlay.addEventListener("click", (e) => {
  if (e.target === removeModalOverlay) removeModalOverlay.classList.add("hidden");
});

removeModalConfirm.addEventListener("click", async () => {
  const file = fileSelect.value;
  removeModalConfirm.disabled = true;

  try {
    const resp = await fetch("/api/remove_file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file }),
    });
    const data = await resp.json();

    if (data.error) {
      showToast(data.error, true);
    } else {
      showToast(data.status);
      removeModalOverlay.classList.add("hidden");
      await loadFiles();
      updateDescription();
    }
  } catch (e) {
    showToast("移除失败", true);
  }

  removeModalConfirm.disabled = false;
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
  }, 2800);
}
