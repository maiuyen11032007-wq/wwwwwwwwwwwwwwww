// SphereAI Controller v10.0 - Clean Light-Blue UI, Before/After Cleaning Comparison & Multi-Dimensional Analytics
let chartInstances = [null, null, null, null];
let rawTableData = [];
let tableColumns = [];
let currentSelectedFile = null;
let isSampleSelected = false;
let currentStage = "idle"; // idle | awaiting_human_gatekeeper | awaiting_human_evaluation | completed

document.addEventListener("DOMContentLoaded", () => {
    console.log("SphereAI v10.0 Initialized");
    initNavigation();
    initCentralHub();
    initHumanApprovalControls();
    initGatekeeperTabs();
    initWorkflowClicks();
    checkCurrentStatus();
});

// View switching logic
function switchView(viewName) {
    document.querySelectorAll(".content-view").forEach(v => v.classList.remove("active-view"));
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) targetView.classList.add("active-view");

    document.querySelectorAll(".nav-item").forEach(item => {
        if (item.getAttribute("data-view") === viewName) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    const titleEl = document.getElementById("current-view-title");
    if (titleEl) {
        if (viewName === "home") titleEl.innerText = "Quy Trình Xử Lý & Phân Tích Dữ Liệu";
        else if (viewName === "dashboard") titleEl.innerText = "Dashboard Phân Tích Đa Chiều Theo Bối Cảnh";
        else if (viewName === "report") titleEl.innerText = "Báo Cáo Phân Tích Dashboard & Định Hướng Trình Cấp Trên (Word)";
        else if (viewName === "excel") titleEl.innerText = "Xem Trước File Excel Đã Làm Sạch";
    }

    const mainArea = document.getElementById("main-content-area");
    if (mainArea) mainArea.scrollTop = 0;
}

function initNavigation() {
    const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");
    const sidebar = document.getElementById("left-sidebar");
    const toggleIcon = document.getElementById("sidebar-toggle-icon");

    if (btnToggleSidebar && sidebar) {
        btnToggleSidebar.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            toggleIcon.innerText = sidebar.classList.contains("collapsed") ? "▶" : "◀";
        });
    }

    const btnMobile = document.getElementById("btn-mobile-menu");
    if (btnMobile && sidebar) {
        btnMobile.addEventListener("click", () => {
            sidebar.classList.toggle("mobile-open");
        });
    }

    document.querySelectorAll("[data-view]").forEach(el => {
        el.addEventListener("click", () => {
            const view = el.getAttribute("data-view");
            if (view) {
                switchView(view);
                if (window.innerWidth <= 900 && sidebar) {
                    sidebar.classList.remove("mobile-open");
                }
            }
        });
    });

    const btnCenterSample = document.getElementById("btn-center-sample");
    if (btnCenterSample) {
        btnCenterSample.addEventListener("click", () => {
            switchView("home");
            currentSelectedFile = null;
            isSampleSelected = true;
            showSelectedFileBadge("Dữ liệu mẫu CRM Bán hàng (54 dòng gốc)");
            updateReadinessState();
        });
    }

    const btnReset = document.getElementById("nav-reset-data");
    if (btnReset) {
        btnReset.addEventListener("click", async () => {
            if (confirm("Bạn có muốn làm mới toàn bộ dữ liệu và quy trình về trạng thái ban đầu?")) {
                try {
                    await fetch("/api/reset", { method: "POST" });
                } catch(e) {}
                resetToEmptyState();
                switchView("home");
            }
        });
    }
}

function initGatekeeperTabs() {
    const btnChanges = document.getElementById("tab-btn-changes");
    const btnPreview = document.getElementById("tab-btn-preview");
    const contentChanges = document.getElementById("tab-content-changes");
    const contentPreview = document.getElementById("tab-content-preview");

    if (btnChanges && btnPreview) {
        btnChanges.addEventListener("click", () => {
            btnChanges.classList.add("active");
            btnPreview.classList.remove("active");
            if (contentChanges) contentChanges.style.display = "block";
            if (contentPreview) contentPreview.style.display = "none";
        });
        btnPreview.addEventListener("click", () => {
            btnPreview.classList.add("active");
            btnChanges.classList.remove("active");
            if (contentPreview) contentPreview.style.display = "block";
            if (contentChanges) contentChanges.style.display = "none";
        });
    }
}

function updateReadinessState() {
    const contextInput = document.getElementById("business-context-input");
    const hasData = (currentSelectedFile !== null || isSampleSelected === true);
    const hasContext = contextInput && contextInput.value.trim().length > 0;

    const dataStatusEl = document.getElementById("ready-data-status");
    const ctxStatusEl = document.getElementById("ready-context-status");
    const btnRun = document.getElementById("btn-run-workflow");
    const btnRunText = document.getElementById("btn-run-text");

    if (dataStatusEl) {
        if (hasData) {
            const srcName = currentSelectedFile ? currentSelectedFile.name : "Dữ liệu mẫu CRM";
            dataStatusEl.className = "ready-item ready-ok";
            dataStatusEl.innerHTML = `<span>✅ 1. Đã chọn: ${srcName}</span>`;
        } else {
            dataStatusEl.className = "ready-item";
            dataStatusEl.innerHTML = `<span>⏳ 1. Chưa có dữ liệu</span>`;
        }
    }

    if (ctxStatusEl) {
        if (hasContext) {
            ctxStatusEl.className = "ready-item ready-ok";
            ctxStatusEl.innerHTML = `<span>✅ 2. Đã nhập bối cảnh doanh nghiệp</span>`;
        } else {
            ctxStatusEl.className = "ready-item";
            ctxStatusEl.innerHTML = `<span>⏳ 2. Chưa nhập bối cảnh doanh nghiệp</span>`;
        }
    }

    if (btnRun && btnRunText) {
        if (hasData && hasContext) {
            btnRun.classList.remove("btn-locked");
            btnRunText.innerText = "Bắt Đầu Phân Tích Theo Quy Trình";
        } else {
            btnRun.classList.add("btn-locked");
            btnRunText.innerText = "Đưa đủ Dữ liệu & Bối cảnh để Bắt đầu phân tích";
        }
    }
}

function initCentralHub() {
    const centerInput = document.getElementById("center-file-input");
    const dropArea = document.getElementById("upload-drop-area");
    const btnRemoveFile = document.getElementById("btn-remove-file");
    const btnRunWorkflow = document.getElementById("btn-run-workflow");
    const contextInput = document.getElementById("business-context-input");

    document.querySelectorAll(".preset-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active-preset"));
            chip.classList.add("active-preset");
            const ctxText = chip.getAttribute("data-context");
            if (contextInput && ctxText) {
                contextInput.value = ctxText;
                updateReadinessState();
            }
        });
    });

    if (contextInput) {
        contextInput.addEventListener("input", () => {
            updateReadinessState();
        });
    }

    function onFileStaged(file) {
        if (!file) return;
        switchView("home");
        currentSelectedFile = file;
        isSampleSelected = false;
        showSelectedFileBadge(`${file.name}`);
        updateReadinessState();
    }

    if (centerInput) {
        centerInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files.length > 0) {
                onFileStaged(e.target.files[0]);
                e.target.value = "";
            }
        });
    }

    if (dropArea) {
        dropArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropArea.classList.add("drag-active");
        });
        dropArea.addEventListener("dragleave", () => {
            dropArea.classList.remove("drag-active");
        });
        dropArea.addEventListener("drop", (e) => {
            e.preventDefault();
            dropArea.classList.remove("drag-active");
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                onFileStaged(e.dataTransfer.files[0]);
            }
        });
    }

    window.addEventListener("dragover", (e) => e.preventDefault());
    window.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onFileStaged(e.dataTransfer.files[0]);
        }
    });

    if (btnRemoveFile) {
        btnRemoveFile.addEventListener("click", () => {
            currentSelectedFile = null;
            isSampleSelected = false;
            document.getElementById("selected-file-badge").style.display = "none";
            document.getElementById("upload-status-title").innerText = "Kéo thả file Excel (.xlsx, .xls) hoặc CSV vào đây";
            updateReadinessState();
        });
    }

    if (btnRunWorkflow) {
        btnRunWorkflow.addEventListener("click", () => {
            const hasData = (currentSelectedFile !== null || isSampleSelected === true);
            const bizContext = contextInput ? contextInput.value.trim() : "";

            if (!hasData && !bizContext) {
                alert("⚠️ Vui lòng chọn File dữ liệu (ở Mục 1) VÀ nhập Bối cảnh doanh nghiệp (ở Mục 2) trước khi bấm Bắt đầu phân tích!");
                return;
            }
            if (!hasData) {
                alert("⚠️ Bạn chưa đưa dữ liệu lên! Vui lòng chọn file Excel/CSV hoặc bấm '⚡ Dùng dữ liệu mẫu CRM' ở Mục 1.");
                return;
            }
            if (!bizContext) {
                alert("⚠️ Bạn chưa nhập Bối cảnh doanh nghiệp! Vui lòng chọn nhanh lĩnh vực hoặc nhập mô tả ở Mục 2.");
                if (contextInput) contextInput.focus();
                return;
            }

            if (currentSelectedFile) {
                uploadAndStartStep1Step2(currentSelectedFile, bizContext);
            } else if (isSampleSelected) {
                loadSampleCRMData(bizContext);
            }
        });
    }

    const searchInput = document.getElementById("table-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            filterPreviewTable(e.target.value.toLowerCase().trim());
        });
    }
}

function initHumanApprovalControls() {
    // TRẠM 1: KIỂM DUYỆT DỮ LIỆU
    const btnGkYes = document.getElementById("btn-human-gk-yes");
    const btnGkNo = document.getElementById("btn-human-gk-no");
    const pillYes1 = document.getElementById("pill-yes-1");
    const pillNo1 = document.getElementById("pill-no-1");
    const loopLabel1 = document.getElementById("loop-label-1");
    const btnConfirmReclean = document.getElementById("btn-confirm-reclean");

    function triggerApproveGatekeeper() {
        if (currentStage !== "awaiting_human_gatekeeper") return;
        approveGatekeeperAndRunStep4();
    }

    function triggerRejectGatekeeper() {
        if (currentStage !== "awaiting_human_gatekeeper") return;
        const drawer = document.getElementById("hr-reclean-options");
        if (drawer) {
            drawer.style.display = drawer.style.display === "none" ? "flex" : "none";
            if (drawer.style.display === "flex") {
                drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        }
    }

    if (btnGkYes) btnGkYes.addEventListener("click", triggerApproveGatekeeper);
    if (pillYes1) pillYes1.addEventListener("click", triggerApproveGatekeeper);
    if (btnGkNo) btnGkNo.addEventListener("click", triggerRejectGatekeeper);
    if (pillNo1) pillNo1.addEventListener("click", triggerRejectGatekeeper);
    if (loopLabel1) loopLabel1.addEventListener("click", triggerRejectGatekeeper);

    // Khi tick vào "Xóa bỏ hẳn dòng trống", tự động bỏ tick "Điền mặc định" và ngược lại
    const chkFill = document.getElementById("chk-fill-missing");
    const chkDrop = document.getElementById("chk-drop-missing");
    if (chkFill && chkDrop) {
        chkDrop.addEventListener("change", () => {
            if (chkDrop.checked) chkFill.checked = false;
        });
        chkFill.addEventListener("change", () => {
            if (chkFill.checked) chkDrop.checked = false;
        });
    }

    if (btnConfirmReclean) {
        btnConfirmReclean.addEventListener("click", () => {
            executeRecleanLoop();
        });
    }

    // TRẠM 2: ĐÁNH GIÁ KẾT QUẢ
    const btnEvalYes = document.getElementById("btn-human-eval-yes");
    const btnEvalNo = document.getElementById("btn-human-eval-no");
    const pillYes2 = document.getElementById("pill-yes-2");
    const pillNo2 = document.getElementById("pill-no-2");
    const loopLabel2 = document.getElementById("loop-label-2");
    const btnConfirmRefine = document.getElementById("btn-confirm-refine");

    function triggerApproveEvaluation() {
        if (currentStage !== "awaiting_human_evaluation") return;
        approveEvaluationAndFinishStep5();
    }

    function triggerRejectEvaluation() {
        if (currentStage !== "awaiting_human_evaluation") return;
        const drawer = document.getElementById("hr-refine-options");
        if (drawer) {
            drawer.style.display = "flex";
            const input = document.getElementById("input-refine-feedback");
            if (input) input.focus();
            drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    }

    if (btnEvalYes) btnEvalYes.addEventListener("click", triggerApproveEvaluation);
    if (pillYes2) pillYes2.addEventListener("click", triggerApproveEvaluation);
    if (btnEvalNo) btnEvalNo.addEventListener("click", triggerRejectEvaluation);
    if (pillNo2) pillNo2.addEventListener("click", triggerRejectEvaluation);
    if (loopLabel2) loopLabel2.addEventListener("click", triggerRejectEvaluation);

    if (btnConfirmRefine) {
        btnConfirmRefine.addEventListener("click", () => {
            executeRefineAnalysisLoop();
        });
    }
}

function showSelectedFileBadge(filename) {
    const badge = document.getElementById("selected-file-badge");
    const nameEl = document.getElementById("selected-file-name");
    const titleEl = document.getElementById("upload-status-title");
    if (nameEl) nameEl.innerText = filename;
    if (badge) badge.style.display = "inline-flex";
    if (titleEl) titleEl.innerText = "Nguồn dữ liệu đã chọn:";
}

function initWorkflowClicks() {
    document.querySelectorAll(".wf-output-card").forEach(card => {
        card.addEventListener("click", () => {
            const view = card.getAttribute("data-view");
            if (view) switchView(view);
        });
    });
}

async function checkCurrentStatus() {
    try {
        const res = await fetch("/api/status");
        const json = await res.json();
        if (json.has_data && json.data) {
            isSampleSelected = true;
            showSelectedFileBadge(json.source || "Dữ liệu đã nạp");
            if (json.business_context) {
                const ctxEl = document.getElementById("business-context-input");
                if (ctxEl && !ctxEl.value) ctxEl.value = json.business_context;
            }
            updateReadinessState();
            renderSessionState(json.data, false);
        } else {
            resetToEmptyState();
        }
    } catch (e) {
        resetToEmptyState();
    }
}

function showLoadingBar(title, subtitle) {
    const bar = document.getElementById("ai-loading-bar");
    const titleEl = document.getElementById("loading-title");
    const subEl = document.getElementById("loading-subtitle");
    if (titleEl && title) titleEl.innerText = title;
    if (subEl && subtitle) subEl.innerText = subtitle;
    if (bar) bar.style.display = "flex";
}

function hideLoadingBar() {
    const bar = document.getElementById("ai-loading-bar");
    if (bar) bar.style.display = "none";
}

// =========================================================================
// API CALLS FOR THE 5-STEP PIPELINE
// =========================================================================

async function uploadAndStartStep1Step2(file, bizContext) {
    if (!file || !bizContext) return;

    showLoadingBar(
        `Đang thực hiện Bước 1 (Nhập file) & Bước 2 (Làm sạch dữ liệu): ${file.name}...`,
        "Đang đối chiếu và chuẩn hóa dữ liệu so với file ban đầu..."
    );

    const formData = new FormData();
    formData.append("file", file);
    formData.append("business_context", bizContext);

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            showSelectedFileBadge(`${file.name} ✓`);
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi xử lý file: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

async function loadSampleCRMData(bizContext) {
    if (!bizContext) return;

    showLoadingBar(
        "Đang thực hiện Bước 1 (Nhập dữ liệu mẫu) & Bước 2 (Làm sạch dữ liệu)...",
        "Đang lọc trùng lặp, điền khuyết ô trống và lập bảng so sánh với file ban đầu..."
    );

    try {
        const res = await fetch("/api/load-sample", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ business_context: bizContext })
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            showSelectedFileBadge("Dữ liệu mẫu CRM ✓");
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi nạp mẫu: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

async function executeRecleanLoop() {
    const dropDup = document.getElementById("chk-drop-dup")?.checked ?? true;
    const fillMissing = document.getElementById("chk-fill-missing")?.checked ?? true;
    const dropMissing = document.getElementById("chk-drop-missing")?.checked ?? false;
    const fixAnomaly = document.getElementById("chk-fix-anomaly")?.checked ?? true;
    const customInst = document.getElementById("input-reclean-custom")?.value.trim() || "";

    showLoadingBar(
        "↩ Đang quay lại Bước 2: Làm sạch lại trên File gốc theo tùy chọn của bạn...",
        "Đang cập nhật báo cáo đối chiếu Trước và Sau làm sạch..."
    );

    try {
        const res = await fetch("/api/gatekeeper/reclean", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                drop_duplicates: dropDup,
                fill_missing: fillMissing,
                drop_missing_rows: dropMissing,
                fix_anomalies: fixAnomaly,
                custom_instruction: customInst
            })
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            const drawer = document.getElementById("hr-reclean-options");
            if (drawer) drawer.style.display = "none";
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi khi làm sạch lại: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

async function approveGatekeeperAndRunStep4() {
    const contextInput = document.getElementById("business-context-input");
    const bizContext = contextInput ? contextInput.value.trim() : "";

    showLoadingBar(
        "✅ Đã duyệt Kiểm duyệt dữ liệu! Đang chạy Bước 4: Phân tích dữ liệu & Tạo Insight...",
        "Gemini AI đang bóc tách 4 chiều Dashboard và soạn Báo cáo trình cấp trên..."
    );

    try {
        const res = await fetch("/api/gatekeeper/approve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ business_context: bizContext })
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi phân tích Bước 4: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

async function executeRefineAnalysisLoop() {
    const feedbackEl = document.getElementById("input-refine-feedback");
    const feedback = feedbackEl ? feedbackEl.value.trim() : "";
    if (!feedback) {
        alert("Vui lòng nhập nội dung bạn muốn AI điều chỉnh và phân tích lại!");
        if (feedbackEl) feedbackEl.focus();
        return;
    }

    const contextInput = document.getElementById("business-context-input");
    const bizContext = contextInput ? contextInput.value.trim() : "";

    showLoadingBar(
        "↩ Đang quay lại Bước 4: Điều chỉnh & Phân tích lại theo yêu cầu của bạn...",
        `Yêu cầu điều chỉnh: "${feedback}"`
    );

    try {
        const res = await fetch("/api/evaluation/refine", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                feedback: feedback,
                business_context: bizContext
            })
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            const drawer = document.getElementById("hr-refine-options");
            if (drawer) drawer.style.display = "none";
            if (feedbackEl) feedbackEl.value = "";
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi khi phân tích lại: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

async function approveEvaluationAndFinishStep5() {
    showLoadingBar(
        "✅ Đã duyệt Đánh giá kết quả! Đang hoàn tất Bước 5: Xuất báo cáo đa định dạng...",
        "Đang mở khóa File Excel, Dashboard 4 chiều và Báo cáo Word trình cấp trên..."
    );

    try {
        const res = await fetch("/api/evaluation/approve", {
            method: "POST"
        });
        const json = await res.json();
        hideLoadingBar();

        if (res.ok && json.status === "success") {
            renderSessionState(json.data, true);
        } else {
            alert("Lỗi hoàn tất Bước 5: " + (json.detail || "Không rõ nguyên nhân"));
        }
    } catch (err) {
        hideLoadingBar();
        alert("Lỗi kết nối máy chủ: " + err.message);
    }
}

// =========================================================================
// RENDER SESSION STATE
// =========================================================================
function renderSessionState(data, autoScroll = false) {
    currentStage = data.stage || "idle";
    const gk = data.gatekeeper;
    const analysis = data.gemini_analysis;
    rawTableData = data.preview || [];
    tableColumns = data.columns || [];

    updateFlowchartNodes(
        currentStage,
        data.cleaning_loop_count || 0,
        data.analysis_loop_count || 0
    );

    if (gk) {
        renderExcelView(data);
    }

    if (analysis) {
        renderDashboardView(analysis, data.business_context);
        renderReportView(analysis, gk);
    }

    const gkPanel = document.getElementById("human-gatekeeper-panel");
    const evalPanel = document.getElementById("human-evaluation-panel");
    const homeBanner = document.getElementById("home-data-banner");
    const topPill = document.getElementById("top-stage-pill");

    if (currentStage === "awaiting_human_gatekeeper") {
        if (topPill) topPill.innerText = "Bước 3: Chờ bạn Kiểm duyệt dữ liệu đã làm sạch";
        updateSidebarDataStatus(true, "Chờ bạn Kiểm duyệt (B3)", data.source);
        if (gkPanel) {
            populateHumanGatekeeperPanel(data);
            gkPanel.style.display = "block";
            if (autoScroll) gkPanel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        if (evalPanel) evalPanel.style.display = "none";
        if (homeBanner) homeBanner.style.display = "none";
    } else if (currentStage === "awaiting_human_evaluation") {
        if (topPill) topPill.innerText = "Bước 4 ➔ 5: Chờ bạn Đánh giá kết quả phân tích";
        updateSidebarDataStatus(true, "Chờ bạn Đánh giá KQ", data.source);
        if (gkPanel) gkPanel.style.display = "none";
        if (evalPanel) {
            populateHumanEvaluationPanel(data);
            evalPanel.style.display = "block";
            if (autoScroll) evalPanel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        if (homeBanner) homeBanner.style.display = "none";
    } else if (currentStage === "completed") {
        if (topPill) topPill.innerText = "Bước 5: Đã hoàn tất & Xuất 3 báo cáo";
        updateSidebarDataStatus(true, analysis ? analysis.domain_detected : "Hoàn tất 5 bước", data.source);
        if (gkPanel) gkPanel.style.display = "none";
        if (evalPanel) evalPanel.style.display = "none";
        if (homeBanner) {
            const bannerTitle = document.getElementById("banner-title");
            if (bannerTitle && analysis) {
                bannerTitle.innerText = `Hoàn tất 5 bước: ${analysis.domain_detected} (${data.total_rows} dòng sạch)`;
            }
            homeBanner.style.display = "flex";
            if (autoScroll) homeBanner.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }
}

function populateHumanGatekeeperPanel(data) {
    const gk = data.gatekeeper.summary;
    const cmp = data.gatekeeper.comparison || {};
    const loopCount = data.cleaning_loop_count || 0;

    document.getElementById("hr-gk-loop-tag").innerText = loopCount > 0 ? `Đã làm sạch lại (${loopCount} lần)` : "Đã làm sạch tự động (Bước 2)";

    // 1. Render 4 Comparison Cards (File ban đầu vs Sau khi làm sạch)
    const beforeHealth = cmp.before_health_score !== undefined ? cmp.before_health_score : gk.health_score;
    const afterHealth = cmp.after_health_score !== undefined ? cmp.after_health_score : gk.health_score;
    document.getElementById("cmp-health-before").innerText = `${beforeHealth}%`;
    document.getElementById("cmp-health-after").innerText = `${afterHealth}%`;
    const healthDiff = (afterHealth - beforeHealth).toFixed(1);
    document.getElementById("cmp-health-note").innerText = healthDiff > 0 ? `Tăng +${healthDiff}% độ sạch dữ liệu` : "Dữ liệu đạt chuẩn hợp lệ";

    const beforeRows = cmp.before_rows !== undefined ? cmp.before_rows : gk.total_records;
    const afterRows = cmp.after_rows !== undefined ? cmp.after_rows : gk.total_records;
    const removedRows = cmp.removed_rows || 0;
    document.getElementById("cmp-rows-before").innerText = `${beforeRows} dòng`;
    document.getElementById("cmp-rows-after").innerText = `${afterRows} dòng`;
    document.getElementById("cmp-rows-note").innerText = removedRows > 0 ? `Đã loại bỏ ${removedRows} dòng trùng/lỗi` : "Giữ nguyên toàn bộ dòng hợp lệ";

    const beforeDup = cmp.before_duplicates !== undefined ? cmp.before_duplicates : 0;
    const afterDup = cmp.after_duplicates !== undefined ? cmp.after_duplicates : gk.duplicate_count;
    document.getElementById("cmp-dup-before").innerText = `${beforeDup} dòng`;
    document.getElementById("cmp-dup-after").innerText = `${afterDup} dòng`;
    document.getElementById("cmp-dup-note").innerText = beforeDup > afterDup ? `Đã xóa ${beforeDup - afterDup} bản ghi trùng lặp` : "Không còn bản ghi trùng lặp";

    const beforeMissing = cmp.before_missing_cells !== undefined ? cmp.before_missing_cells : 0;
    const afterMissing = cmp.after_missing_cells !== undefined ? cmp.after_missing_cells : 0;
    document.getElementById("cmp-missing-before").innerText = `${beforeMissing} ô trống`;
    document.getElementById("cmp-missing-after").innerText = `${afterMissing} ô trống`;
    if (cmp.dropped_missing_rows > 0) {
        document.getElementById("cmp-missing-note").innerText = `Đã xóa ${cmp.dropped_missing_rows} dòng có ô trống`;
    } else if (cmp.filled_missing_cells > 0) {
        document.getElementById("cmp-missing-note").innerText = `Đã tự động điền chuẩn hóa ${cmp.filled_missing_cells} ô trống`;
    } else {
        document.getElementById("cmp-missing-note").innerText = "Không có ô bị bỏ trống";
    }

    // 2. Danh sách tóm tắt các hành động làm sạch so với file gốc
    const actionsEl = document.getElementById("hr-gk-actions-list");
    const actions = data.gatekeeper.actions_taken || [];
    if (actionsEl) {
        const bulletItems = actions.map(a => `<li>✓ ${a}</li>`).join("");
        actionsEl.innerHTML = `
            <strong>🧹 Tổng hợp các xử lý ở Bước 2 so với File ban đầu:</strong>
            <ul style="margin-top: 4px; padding-left: 18px; list-style: none;">${bulletItems}</ul>
        `;
    }

    // 3. Render Tab 1: Bảng chi tiết từng dòng/ô đã thay đổi so với File ban đầu (change_logs)
    const changeLogs = cmp.change_logs || [];
    const countBadge = document.getElementById("changes-count-badge");
    if (countBadge) countBadge.innerText = changeLogs.length;

    const changesTbody = document.getElementById("hr-changes-tbody");
    if (changesTbody) {
        if (changeLogs.length === 0) {
            changesTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 16px; color: #16a34a; font-weight: 700;">File ban đầu đã sạch chuẩn, không phát sinh lỗi trùng lặp hay ô trống cần thay thế.</td></tr>`;
        } else {
            changesTbody.innerHTML = changeLogs.map(log => `
                <tr>
                    <td><strong>${log.row}</strong></td>
                    <td><strong>${log.column}</strong></td>
                    <td><span class="badge-before-val">${log.before}</span></td>
                    <td><span class="badge-after-val">${log.after}</span></td>
                    <td>${log.action}</td>
                </tr>
            `).join("");
        }
    }

    // 4. Render Tab 2: Bảng xem trước dữ liệu hoàn chỉnh sau làm sạch
    const thead = document.getElementById("hr-gk-thead");
    const tbody = document.getElementById("hr-gk-tbody");
    const rows = (data.preview || []).slice(0, 12);
    const cols = data.columns || [];

    if (thead && cols.length > 0) {
        thead.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
    }
    if (tbody) {
        tbody.innerHTML = rows.map(r => {
            return `<tr>${cols.map(c => `<td>${r[c] !== undefined ? r[c] : ""}</td>`).join("")}</tr>`;
        }).join("");
    }
}

function populateHumanEvaluationPanel(data) {
    const analysis = data.gemini_analysis || {};
    const loopCount = data.analysis_loop_count || 0;

    document.getElementById("hr-eval-loop-tag").innerText = loopCount > 0 ? `Đã điều chỉnh & phân tích lại (${loopCount} lần)` : "Đánh giá lần #1";

    const domainEl = document.getElementById("hr-eval-domain");
    if (domainEl) {
        const dimsList = (analysis.charts || []).map(c => c.dimension_badge || c.title).join(" • ");
        const feedbackHtml = analysis.human_feedback_applied
            ? `<br><strong>🔄 Yêu cầu điều chỉnh đã áp dụng:</strong> <em>"${analysis.human_feedback_applied}"</em>`
            : "";
        domainEl.innerHTML = `
            <strong>🎯 Lĩnh vực nhận diện:</strong> ${analysis.domain_detected || ""}<br>
            <strong>📊 4 Chiều phân tích trên Dashboard:</strong> ${dimsList}<br>
            <strong>📌 Tóm tắt điều hành trình lãnh đạo:</strong> ${analysis.dataset_summary || ""}
            ${feedbackHtml}
        `;
    }

    const kpisEl = document.getElementById("hr-eval-kpis");
    if (kpisEl) {
        kpisEl.innerHTML = (analysis.kpis || []).map(k => `
            <div class="hr-kpi-mini">
                <span>${k.label}</span>
                <strong>${k.value}</strong>
            </div>
        `).join("");
    }

    const prioEl = document.getElementById("hr-eval-priorities");
    if (prioEl) {
        const roadmap = analysis.strategic_roadmap || {};
        const proposals = (roadmap.proposals_for_upper_management || []).slice(0, 3).map(pr => `<li>${pr}</li>`).join("");
        prioEl.innerHTML = `
            <strong>📌 Kiến nghị trình Cấp trên phê duyệt (trong Báo cáo Word):</strong>
            <ul style="margin-top: 6px; padding-left: 20px;">${proposals}</ul>
        `;
    }
}

function updateFlowchartNodes(stage, cleanLoops, analysisLoops) {
    const s1 = document.getElementById("wf-step-1");
    const s2 = document.getElementById("wf-step-2");
    const d1 = document.getElementById("wf-decision-1");
    const s4 = document.getElementById("wf-step-4");
    const d2 = document.getElementById("wf-decision-2");
    const s5 = document.getElementById("wf-step-5");

    const stat1 = document.getElementById("status-step-1");
    const stat2 = document.getElementById("status-step-2");
    const stat4 = document.getElementById("status-step-4");
    const stat5 = document.getElementById("status-step-5");

    [s1, s2, s4, s5].forEach(el => { if (el) el.classList.remove("active-step", "done-step"); });
    [d1, d2].forEach(el => { if (el) el.classList.remove("active-diamond", "done-diamond", "waiting-human"); });

    if (stage === "awaiting_human_gatekeeper") {
        if (s1) { s1.classList.add("done-step"); if (stat1) stat1.innerText = "✓ Đã nhập liệu"; }
        if (s2) { s2.classList.add("done-step"); if (stat2) stat2.innerText = cleanLoops > 0 ? `✓ Đã làm sạch lại (${cleanLoops})` : "✓ Đã làm sạch"; }
        if (d1) d1.classList.add("waiting-human");
        if (stat4) stat4.innerText = "Chờ bạn duyệt B3";
        if (stat5) stat5.innerText = "Chờ duyệt KQ";
    } else if (stage === "awaiting_human_evaluation") {
        if (s1) { s1.classList.add("done-step"); if (stat1) stat1.innerText = "✓ Đã nhập liệu"; }
        if (s2) { s2.classList.add("done-step"); if (stat2) stat2.innerText = "✓ Đã làm sạch"; }
        if (d1) d1.classList.add("done-diamond");
        if (s4) { s4.classList.add("done-step"); if (stat4) stat4.innerText = analysisLoops > 0 ? `✓ Đã phân tích lại (${analysisLoops})` : "✓ Đã tạo insight"; }
        if (d2) d2.classList.add("waiting-human");
        if (stat5) stat5.innerText = "Chờ bạn duyệt B4";
    } else if (stage === "completed") {
        if (s1) { s1.classList.add("done-step"); if (stat1) stat1.innerText = "✓ Đã nhập liệu"; }
        if (s2) { s2.classList.add("done-step"); if (stat2) stat2.innerText = "✓ Đã làm sạch"; }
        if (d1) d1.classList.add("done-diamond");
        if (s4) { s4.classList.add("done-step"); if (stat4) stat4.innerText = "✓ Đã tạo insight"; }
        if (d2) d2.classList.add("done-diamond");
        if (s5) { s5.classList.add("done-step", "active-step"); if (stat5) stat5.innerText = "✓ Đã xuất 3 báo cáo!"; }
    } else {
        if (stat1) stat1.innerText = "Chờ nhập liệu";
        if (stat2) stat2.innerText = "Chờ làm sạch";
        if (stat4) stat4.innerText = "Chờ phân tích";
        if (stat5) stat5.innerText = "Chờ duyệt KQ";
    }
}

function updateSidebarDataStatus(hasData, domain, source) {
    const dot = document.getElementById("nav-data-dot");
    const text = document.getElementById("nav-data-text");
    const sub = document.getElementById("nav-data-sub");

    if (hasData) {
        if (dot) dot.className = "status-dot dot-ready";
        if (text) text.innerText = domain || "Đang xử lý";
        if (sub) sub.innerText = source || "Quy trình 5 bước";
    } else {
        if (dot) dot.className = "status-dot dot-idle";
        if (text) text.innerText = "Chưa có dữ liệu";
        if (sub) sub.innerText = "Chọn file & bối cảnh để bắt đầu";
    }
}

function resetToEmptyState() {
    currentStage = "idle";
    currentSelectedFile = null;
    isSampleSelected = false;
    updateSidebarDataStatus(false, "", "");
    rawTableData = [];
    tableColumns = [];
    updateFlowchartNodes("idle", 0, 0);
    updateReadinessState();

    const topPill = document.getElementById("top-stage-pill");
    if (topPill) topPill.innerText = "Bước 1: Nhập dữ liệu & Bối cảnh";

    const gkPanel = document.getElementById("human-gatekeeper-panel");
    const evalPanel = document.getElementById("human-evaluation-panel");
    if (gkPanel) gkPanel.style.display = "none";
    if (evalPanel) evalPanel.style.display = "none";

    const fileBadge = document.getElementById("selected-file-badge");
    if (fileBadge) fileBadge.style.display = "none";
    const uploadTitle = document.getElementById("upload-status-title");
    if (uploadTitle) uploadTitle.innerText = "Kéo thả file Excel (.xlsx, .xls) hoặc CSV vào đây";

    const homeBanner = document.getElementById("home-data-banner");
    if (homeBanner) homeBanner.style.display = "none";

    document.getElementById("dash-empty").style.display = "flex";
    document.getElementById("dash-content").style.display = "none";
    document.getElementById("report-empty").style.display = "flex";
    document.getElementById("report-content").style.display = "none";
    document.getElementById("excel-empty").style.display = "flex";
    document.getElementById("excel-content").style.display = "none";
}

// =========================================================================
// DASHBOARD RENDERING (6 KPIs + 4 MULTI-DIMENSIONAL CHARTS)
// =========================================================================
function renderDashboardView(analysis, businessContext) {
    document.getElementById("dash-empty").style.display = "none";
    document.getElementById("dash-content").style.display = "block";

    const domainDesc = document.getElementById("dash-domain-desc");
    if (domainDesc) domainDesc.innerText = `Lĩnh vực: ${analysis.domain_detected} — ${analysis.dataset_summary}`;

    const ctxTextEl = document.getElementById("dash-context-text");
    if (ctxTextEl) {
        ctxTextEl.innerText = `${businessContext || analysis.business_context || ""} (${analysis.business_context_applied || ""})`;
    }

    const kpiContainer = document.getElementById("kpi-cards-container");
    kpiContainer.innerHTML = "";
    (analysis.kpis || []).forEach(k => {
        const detailHtml = k.analysis_detail ? `<div class="kpi-analysis-detail">📌 ${k.analysis_detail}</div>` : "";
        kpiContainer.innerHTML += `
            <div class="kpi-card ${k.color || 'blue'}">
                <div class="kpi-label">${k.label}</div>
                <div class="kpi-value">${k.value}</div>
                <div class="kpi-sub">${k.sub}</div>
                ${detailHtml}
            </div>
        `;
    });

    const charts = analysis.charts || [];
    for (let i = 0; i < 4; i++) {
        const idx = i + 1;
        const ch = charts[i];
        const badgeEl = document.getElementById(`chart-${idx}-badge`);
        const titleEl = document.getElementById(`chart-${idx}-title`);
        const insightEl = document.getElementById(`chart-${idx}-insight`);
        const cardEl = document.getElementById(`chartCanvas${idx}`)?.closest(".chart-glass-card");

        if (ch) {
            if (cardEl) cardEl.style.display = "block";
            if (badgeEl) badgeEl.innerText = ch.dimension_badge || `Chiều phân tích ${idx}`;
            if (titleEl) titleEl.innerText = ch.title || `Biểu Đồ ${idx}`;
            if (insightEl) {
                insightEl.innerHTML = `<strong>💡 Phân tích chiều dữ liệu:</strong> ${ch.insight_commentary || ""}`;
            }
            renderSingleChart(`chartCanvas${idx}`, ch, i);
        } else if (cardEl) {
            cardEl.style.display = "none";
        }
    }

    const prioritiesContainer = document.getElementById("dash-priorities-list");
    prioritiesContainer.innerHTML = "";
    (analysis.top_5_priorities || []).forEach(p => {
        prioritiesContainer.innerHTML += `
            <div class="priority-row">
                <div class="priority-rank">#${p.rank}</div>
                <div class="priority-details">
                    <div class="priority-main">
                        <strong>${p.name}</strong>
                        <span class="priority-tag">${p.category}</span>
                        <span class="priority-metric">${p.metric}</span>
                    </div>
                    <div class="priority-reason">${p.reason}</div>
                    <div class="priority-action">💡 <strong>Giải pháp thực thi:</strong> ${p.recommended_action}</div>
                </div>
            </div>
        `;
    });
}

function renderSingleChart(canvasId, chartConfig, arrayIndex) {
    if (typeof Chart === "undefined") return;
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[arrayIndex]) {
        chartInstances[arrayIndex].destroy();
    }

    const ctx = canvas.getContext("2d");
    const rawType = chartConfig.type || "bar";
    let chartType = "bar";
    let indexAxis = "x";

    if (rawType === "doughnut" || rawType === "pie") {
        chartType = "doughnut";
    } else if (rawType === "line") {
        chartType = "line";
    } else if (rawType === "horizontalBar") {
        chartType = "bar";
        indexAxis = "y";
    }

    const palette = ["#2563eb", "#7c3aed", "#16a34a", "#ea580c", "#0284c7", "#d97706", "#dc2626"];
    const labels = chartConfig.labels || [];
    const values = chartConfig.values || [];

    chartInstances[arrayIndex] = new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: chartConfig.unit || chartConfig.title || "Số liệu",
                data: values,
                backgroundColor: chartType === "line" ? "rgba(37, 99, 235, 0.15)" : palette.slice(0, Math.max(labels.length, 1)),
                borderColor: chartType === "line" ? "#2563eb" : undefined,
                borderWidth: chartType === "line" ? 2.5 : 1,
                fill: chartType === "line",
                tension: 0.3,
                borderRadius: chartType === "bar" ? 6 : 0
            }]
        },
        options: {
            indexAxis: indexAxis,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: chartType === "doughnut" ? "right" : "top" }
            }
        }
    });
}

// =========================================================================
// UPPER-MANAGEMENT WORD REPORT RENDERING
// =========================================================================
function renderReportView(analysis, gk) {
    document.getElementById("report-empty").style.display = "none";
    document.getElementById("report-content").style.display = "block";

    const summary = gk ? gk.summary : {};
    const cmp = (gk && gk.comparison) ? gk.comparison : {};
    const descEl = document.getElementById("report-domain-desc");
    if (descEl) {
        descEl.innerText = `Tờ trình & Báo cáo phân tích số liệu Dashboard trình Ban Giám đốc — Lĩnh vực: ${analysis.domain_detected}`;
    }

    const reportPaper = document.getElementById("report-paper-body");
    const kpis = analysis.kpis || [];
    const charts = analysis.charts || [];
    const top5 = analysis.top_5_priorities || [];
    const roadmap = analysis.strategic_roadmap || {};
    const nowStr = new Date().toLocaleDateString("vi-VN");

    const kpiRowsHtml = kpis.map(k => `
        <tr>
            <td><strong>${k.label || ""}</strong></td>
            <td><strong style="color: #166534;">${k.value || ""}</strong></td>
            <td>${k.analysis_detail || k.sub || ""}</td>
        </tr>
    `).join("");

    const chartsHtml = charts.map((ch, i) => {
        const labels = ch.labels || [];
        const vals = ch.values || [];
        const unit = ch.unit || "Đơn vị";
        const totalV = vals.reduce((acc, v) => acc + (Number(v) || 0), 0) || 1;

        const rows = labels.map((lbl, rIdx) => {
            const val = vals[rIdx] !== undefined ? vals[rIdx] : 0;
            const pct = ((Number(val) || 0) / totalV * 100).toFixed(1);
            const valFmt = (typeof val === "number" && val >= 100) ? val.toLocaleString("vi-VN") : val;
            return `
                <tr>
                    <td>${lbl}</td>
                    <td><strong>${valFmt} ${unit}</strong></td>
                    <td>${pct}%</td>
                </tr>
            `;
        }).join("");

        return `
            <h3>${i + 1}. ${ch.dimension_badge || `Chiều phân tích ${i + 1}`}: ${ch.title || ""}</h3>
            <p><strong>• Phân tích & Nhận định số liệu:</strong> ${ch.insight_commentary || ""}</p>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Phân nhóm / Hạng mục trên biểu đồ</th>
                        <th>Giá trị đo lường (${unit})</th>
                        <th>Tỷ trọng đóng góp (%)</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }).join("");

    const top5RowsHtml = top5.map(p => `
        <tr>
            <td><strong>#${p.rank}</strong></td>
            <td><strong>${p.name}</strong><br><small>${p.category}</small></td>
            <td><strong>${p.metric}</strong></td>
            <td>${p.reason}</td>
            <td><strong style="color: #b45309;">${p.recommended_action}</strong></td>
        </tr>
    `).join("");

    const bottlenecksHtml = (roadmap.bottlenecks_and_risks || []).map(b => `<li>${b}</li>`).join("");
    const shortTermHtml = (roadmap.short_term_actions || []).map(s => `<li>${s}</li>`).join("");
    const longTermHtml = (roadmap.medium_long_term_orientation || []).map(l => `<li>${l}</li>`).join("");
    const proposalsHtml = (roadmap.proposals_for_upper_management || []).map(pr => `<li><strong>${pr}</strong></li>`).join("");

    reportPaper.innerHTML = `
        <div class="report-admin-header">
            <div>
                <strong>HỆ THỐNG PHÂN TÍCH QUẢN TRỊ SPHEREAI</strong><br>
                <span>BỘ PHẬN PHÂN TÍCH DỮ LIỆU &amp; CHIẾN LƯỢC</span>
            </div>
            <div>
                <strong>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</strong><br>
                <strong>Độc lập - Tự do - Hạnh phúc</strong><br>
                <em>Ngày lập báo cáo: ${nowStr}</em>
            </div>
        </div>

        <div class="report-main-heading">
            <h1>${analysis.report_title || `BÁO CÁO PHÂN TÍCH QUẢN TRỊ & ĐỊNH HƯỚNG PHÁT TRIỂN - ${(analysis.domain_detected || "").toUpperCase()}`}</h1>
            <div class="sub-kính-trình">Kính trình: Ban Giám đốc / Cấp Lãnh đạo có thẩm quyền phê duyệt</div>
        </div>

        <h2>I. BỐI CẢNH DOANH NGHIỆP &amp; TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)</h2>
        <p><strong>1. Bối cảnh &amp; Bài toán doanh nghiệp đang gặp phải:</strong> ${analysis.business_context || ""}</p>
        <p><strong>2. Phương pháp thiết lập các chiều phân tích Dashboard:</strong> ${analysis.business_context_applied || ""}</p>
        <p><strong>3. Tóm tắt kết quả điều hành trình Lãnh đạo:</strong> ${analysis.dataset_summary || ""}</p>
        <table class="report-table">
            <thead>
                <tr>
                    <th>Chỉ tiêu kiểm duyệt &amp; Làm sạch dữ liệu đầu vào (Bước 2 &amp; Bước 3)</th>
                    <th>Kết quả đối chiếu (Trước ➔ Sau làm sạch)</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Quy mô bản ghi dữ liệu</td><td>File ban đầu: ${cmp.before_rows || summary.total_records} dòng ➔ Sau làm sạch: <strong>${summary.total_records || 0} bản ghi sạch</strong></td></tr>
                <tr><td>Điểm chất lượng dữ liệu (Health Score)</td><td>File ban đầu: ${cmp.before_health_score || 0}% ➔ Sau làm sạch: <strong>${summary.health_score || 100}% (Đã duyệt hợp lệ)</strong></td></tr>
                <tr><td>Xử lý dữ liệu bị trống (Missing Values)</td><td>Đã tự động chuẩn hóa &amp; điền khuyết <strong>${cmp.filled_missing_cells || 0} ô bị trống</strong></td></tr>
                <tr><td>Xử lý bản ghi trùng lặp (Duplicates)</td><td>Đã lọc bỏ <strong>${cmp.removed_duplicates || 0} bản ghi trùng lặp</strong></td></tr>
            </tbody>
        </table>

        <h2>II. PHÂN TÍCH CHI TIẾT HỆ THỐNG CHỈ SỐ KPI TRÊN DASHBOARD</h2>
        <p>Bảng dưới đây phân tích chi tiết từng chỉ số đo lường cốt lõi trên Dashboard và tác động trực tiếp đến mục tiêu của doanh nghiệp:</p>
        <table class="report-table">
            <thead>
                <tr>
                    <th>Chỉ số KPI trên Dashboard</th>
                    <th>Giá trị đo lường</th>
                    <th>Phân tích ý nghĩa quản trị &amp; Nguyên nhân</th>
                </tr>
            </thead>
            <tbody>${kpiRowsHtml}</tbody>
        </table>

        <h2>III. PHÂN TÍCH SÂU THEO 4 CHIỀU DỮ LIỆU TRÊN DASHBOARD</h2>
        <p>Hệ thống đã bóc tách số liệu theo 4 chiều phân tích hợp lý với bối cảnh doanh nghiệp. Dưới đây là bảng số liệu và nhận định cho từng chiều:</p>
        ${chartsHtml}

        <h2>IV. NHẬN DIỆN ĐIỂM NGHẼN, RỦI RO &amp; TOP 5 TRỌNG TÂM CẦN XỬ LÝ NGAY</h2>
        <h3>1. Các điểm nghẽn và rủi ro trọng yếu phát hiện từ số liệu Dashboard:</h3>
        <ul>${bottlenecksHtml}</ul>

        <h3>2. Danh mục Top 5 đối tượng / hạng mục trọng tâm cần ưu tiên nguồn lực xử lý:</h3>
        <table class="report-table">
            <thead>
                <tr>
                    <th>Hạng</th>
                    <th>Đối tượng / Hạng mục</th>
                    <th>Chỉ số</th>
                    <th>Nguyên nhân / Lý do ưu tiên</th>
                    <th>Giải pháp hành động cụ thể</th>
                </tr>
            </thead>
            <tbody>${top5RowsHtml}</tbody>
        </table>

        <h2>V. ĐỊNH HƯỚNG PHÁT TRIỂN TIẾP THEO &amp; KIẾN NGHỊ TRÌNH CẤP TRÊN PHÊ DUYỆT</h2>
        <h3>1. Giải pháp hành động ngắn hạn (Trong 30 ngày tới - Tháo gỡ điểm nghẽn tức thời):</h3>
        <ul>${shortTermHtml}</ul>

        <h3>2. Định hướng phát triển trung và dài hạn (Quý tới / 6 - 12 tháng):</h3>
        <ul>${longTermHtml}</ul>

        <h3>3. Kiến nghị &amp; Đề xuất trình Cấp trên / Ban Giám đốc xem xét phê duyệt:</h3>
        <ul>${proposalsHtml}</ul>

        <div class="report-sig-box">
            <div>
                <strong>NGƯỜI LẬP BÁO CÁO / ĐƠN VỊ TRÌNH</strong><br>
                <em>(Ký và ghi rõ họ tên)</em><br><br><br><br>
            </div>
            <div>
                <strong>Ý KIẾN PHÊ DUYỆT CỦA CẤP TRÊN / BAN GIÁM ĐỐC</strong><br>
                <em>(Phê duyệt định hướng &amp; giao chỉ tiêu thực hiện)</em><br><br><br><br>
            </div>
        </div>
    `;
}

// ---------------- EXCEL VIEW RENDERING ----------------
function renderExcelView(data) {
    document.getElementById("excel-empty").style.display = "none";
    document.getElementById("excel-content").style.display = "block";

    const gk = data.gatekeeper.summary;
    const cmp = data.gatekeeper.comparison || {};
    document.getElementById("gk-stat-health").innerText = `${cmp.before_health_score || 0}% ➔ ${gk.health_score}%`;
    document.getElementById("gk-stat-decision").innerText = gk.decision || "Đã làm sạch";
    document.getElementById("gk-stat-valid").innerText = `${cmp.before_rows || gk.total_records} ➔ ${gk.total_records} dòng`;
    document.getElementById("gk-stat-missing").innerText = `${cmp.filled_missing_cells || 0} ô`;
    document.getElementById("gk-stat-dup").innerText = `${cmp.removed_duplicates || 0} dòng`;

    renderPreviewTable(rawTableData);
}

function renderPreviewTable(rows) {
    const thead = document.getElementById("preview-thead");
    const tbody = document.getElementById("preview-tbody");
    const countLabel = document.getElementById("table-rows-count");

    if (countLabel) countLabel.innerText = `Hiển thị ${rows.length} / ${rawTableData.length} dòng mẫu`;

    if (tableColumns.length > 0) {
        thead.innerHTML = `<tr>${tableColumns.map(c => `<th>${c}</th>`).join('')}</tr>`;
    } else if (rows.length > 0) {
        thead.innerHTML = `<tr>${Object.keys(rows[0]).map(c => `<th>${c}</th>`).join('')}</tr>`;
    }

    if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${tableColumns.length || 5}" style="text-align: center; color: #94a3b8; padding: 24px;">Không tìm thấy bản ghi phù hợp</td></tr>`;
        return;
    }

    tbody.innerHTML = rows.map(r => {
        const cells = (tableColumns.length > 0 ? tableColumns : Object.keys(r)).map(col => {
            const val = r[col] !== undefined ? r[col] : "";
            return `<td>${val}</td>`;
        }).join('');
        return `<tr>${cells}</tr>`;
    }).join('');
}

function filterPreviewTable(query) {
    if (!query) {
        renderPreviewTable(rawTableData);
        return;
    }
    const filtered = rawTableData.filter(row => {
        return Object.values(row).some(v => String(v).toLowerCase().includes(query));
    });
    renderPreviewTable(filtered);
}
