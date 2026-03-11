const API = "<API_URL>";
const MODEL_STORAGE_KEY = "selectedModel";

let currentJob = null;
let currentJobId = null; // DB row id from Jobs.id (required by /analyze_job)
let activeJobLink = "";
let jobExistsInDatabase = false;
let analysisReady = false;
let isBusy = false;

window.onload = () => {
    const token = getStoredToken();

    if (token) {
        showApp();
    } else {
        showLogin();
    }
};

function showLogin() {
    document.getElementById("loginView").style.display = "block";
    document.getElementById("appView").style.display = "none";
}

function showApp() {
    document.getElementById("loginView").style.display = "none";
    document.getElementById("appView").style.display = "block";
    clearStatus();
    loadModels();
    initializePopupState();
}

function setStatus(message, type = "info") {
    const status = document.getElementById("statusMessage");
    status.style.display = "block";
    status.className = `status ${type}`;
    status.textContent = message;
}

function clearStatus() {
    const status = document.getElementById("statusMessage");
    status.style.display = "none";
    status.className = "status";
    status.textContent = "";
}

function getStoredToken() {
    const token = (localStorage.getItem("token") || "").trim();
    return token || null;
}

function extractAuthToken(data) {
    if (!data || typeof data !== "object") {
        return null;
    }

    const token = data.token || data.access_token || data.jwt || data.auth_token || "";
    return typeof token === "string" && token.trim() ? token.trim() : null;
}

function getSelectedModel() {
    return document.getElementById("modelSelect").value || "";
}

async function parseApiResponse(res) {
    const text = await res.text();

    if (!text) {
        return { data: null, text: "" };
    }

    try {
        return { data: JSON.parse(text), text };
    } catch (_error) {
        return { data: null, text };
    }
}

function getApiError(res, data, fallbackMessage) {
    if (data && typeof data === "object" && typeof data.error === "string") {
        return data.error;
    }

    return `${fallbackMessage} (HTTP ${res.status})`;
}

async function requestWithRouteFallback(routeConfigs) {
    let lastResponse = null;

    for (const config of routeConfigs) {
        const res = await fetch(`${API}${config.path}`, config.options);
        if (res.status !== 404) {
            return res;
        }
        lastResponse = res;
    }

    return lastResponse;
}

function normalizeJobLink(link) {
    if (typeof link !== "string") {
        return "";
    }

    return link.trim().replace(/\/$/, "");
}

function normalizeJobPayload(payload) {
    const source = payload && typeof payload === "object"
        ? (payload.job_data && typeof payload.job_data === "object" ? payload.job_data : payload)
        : {};

    return {
        ...source,
        scrape_success: payload && typeof payload === "object" ? payload.scrape_success : undefined,
        id: source.id ?? payload.id ?? null,
        job_id: source.job_id ?? payload.job_id ?? null,
        title: source.title ?? source.job_title ?? null,
        company: source.company ?? null,
        location: source.location ?? null,
        experience: source.experience ?? source.experience_required ?? null,
        job_link: source.job_link ?? source.url ?? source.link ?? null,
        progress: source.progress ?? null
    };
}

function formatJobValue(value) {
    if (value === null || value === undefined || value === "") {
        return "Not found";
    }

    return value;
}

function countFilledCoreFields(job) {
    return [job.title, job.company, job.location, job.experience]
        .filter((value) => value !== null && value !== undefined && String(value).trim() !== "")
        .length;
}

function setVisible(id, isVisible) {
    document.getElementById(id).style.display = isVisible ? "block" : "none";
}

function setModelVisibility(isVisible) {
    const display = isVisible ? "block" : "none";
    document.querySelector('label[for="modelSelect"]').style.display = display;
    document.getElementById("modelSelect").style.display = display;
    document.getElementById("modelError").style.display = display;
}

function setBusyState(flag, message = "") {
    isBusy = flag;
    const appButtons = document.querySelectorAll("#appView button");
    appButtons.forEach((button) => {
        button.disabled = flag;
    });

    const loading = document.getElementById("loading");
    if (flag && message) {
        loading.innerText = message;
        loading.style.display = "block";
    } else if (!flag) {
        loading.style.display = "none";
        loading.innerText = "Parsing job description...";
        updateActionButtons();
    }
}

function clampScore(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
        return 0;
    }

    return Math.max(0, Math.min(100, Math.round(numeric)));
}

function getScoreColor(score) {
    if (score >= 71) {
        return "#16a34a";
    }
    if (score >= 41) {
        return "#f59e0b";
    }
    return "#dc2626";
}

function normalizeSkills(value) {
    if (Array.isArray(value)) {
        return value.filter((item) => String(item).trim() !== "");
    }

    if (typeof value !== "string") {
        return [];
    }

    const text = value.trim();
    if (!text || text.toLowerCase() === "none" || text.toLowerCase() === "null") {
        return [];
    }

    try {
        const parsed = JSON.parse(text.replace(/'/g, "\""));
        if (Array.isArray(parsed)) {
            return parsed.filter((item) => String(item).trim() !== "");
        }
    } catch (_error) {
        // fallback below
    }

    return text
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item !== "");
}

function extractModels(payload) {
    if (Array.isArray(payload)) {
        return payload;
    }

    if (!payload || typeof payload !== "object") {
        return [];
    }

    const candidates = [
        payload.models,
        payload.available_models,
        payload.llms,
        payload.data
    ];

    for (const candidate of candidates) {
        if (Array.isArray(candidate)) {
            return candidate;
        }
    }

    return [];
}

function renderModelOptions(models) {
    const select = document.getElementById("modelSelect");
    const modelError = document.getElementById("modelError");
    const validModels = models
        .map((model) => {
            if (typeof model === "string") {
                return model.trim();
            }

            if (model && typeof model === "object") {
                const value = model.model || model.name || model.id || "";
                return typeof value === "string" ? value.trim() : "";
            }

            return "";
        })
        .filter((model) => model !== "");
    const previous = localStorage.getItem(MODEL_STORAGE_KEY);

    select.innerHTML = "";

    if (!validModels.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Default";
        select.appendChild(option);
        modelError.innerText = "";
        return;
    }

    for (const model of validModels) {
        const option = document.createElement("option");
        option.value = model;
        option.textContent = model;
        select.appendChild(option);
    }

    if (previous && validModels.includes(previous)) {
        select.value = previous;
    }

    modelError.innerText = "";
}

async function loadModels() {
    const modelError = document.getElementById("modelError");

    try {
        const res = await fetch(`${API}/check_models`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({})
        });
        const { data: payload } = await parseApiResponse(res);

        if (!res.ok) {
            throw new Error(getApiError(res, payload, "Failed to load models"));
        }

        renderModelOptions(extractModels(payload));
    } catch (error) {
        renderModelOptions([]);
        modelError.innerText = error.message || "Failed to load models";
    }
}

function displayJob(job) {
    currentJob = job;

    const div = document.getElementById("jobDetails");
    const detailsMarkup = `
    <p><b>Title:</b> ${formatJobValue(job.title)}</p>
    <p><b>Company:</b> ${formatJobValue(job.company)}</p>
    <p><b>Location:</b> ${formatJobValue(job.location)}</p>
    <p><b>Experience:</b> ${formatJobValue(job.experience)}</p>
    <p><b>Progress:</b> ${formatJobValue(job.progress || "Checking")}</p>
    `;

    div.innerHTML = detailsMarkup;
    setVisible("jobDetails", !analysisReady);

    updateActionButtons();
}

function renderAnalysisResult(result) {
    const normalized = result && typeof result === "object" && result.analysis
        ? result.analysis
        : result;
    const score = clampScore(normalized && normalized.score);

    const matchedSkills = normalizeSkills(
        normalized && (normalized.matched_skills || normalized.matchedSkills || normalized["Matched Skills"])
    );
    const missingSkills = normalizeSkills(
        normalized && (normalized.missing_skills || normalized.missingSkills || normalized["Missing Skills"])
    );
    const color = getScoreColor(score);

    document.getElementById("analysis").innerHTML = `
    <div class="analysisTop">
        <div class="scoreRing" style="--score:${score};--ring-color:${color};">
            <div class="scoreInner">${score}%</div>
        </div>
    </div>
    <p>Matching Skills:</p>
    <ul>
        ${matchedSkills.length ? matchedSkills.map((skill) => `<li>${skill}</li>`).join("") : "<li>None</li>"}
    </ul>
    <p>Missing Skills:</p>
    <ul>
        ${missingSkills.length ? missingSkills.map((skill) => `<li>${skill}</li>`).join("") : "<li>None</li>"}
    </ul>
    `;

    analysisReady = true;
    setVisible("analysis", true);
    setVisible("jobDetails", false);
    updateActionButtons();
}

function updateActionButtons() {
    const sendButton = document.getElementById("send");
    const analyseButton = document.getElementById("analyse");

    if (analysisReady) {
        setModelVisibility(false);
        sendButton.style.display = "none";
        analyseButton.style.display = "none";
        return;
    } else {
        setModelVisibility(true);
        sendButton.style.display = "block";
    }

    if (!activeJobLink) {
        sendButton.disabled = true;
        sendButton.classList.add("disabled");
        sendButton.textContent = "Open a website tab";
        analyseButton.style.display = "none";
    } else if (jobExistsInDatabase) {
        sendButton.disabled = true;
        sendButton.classList.add("disabled");
        sendButton.textContent = "Page Already Saved";
        analyseButton.style.display = "block";
    } else {
        sendButton.disabled = false;
        sendButton.classList.remove("disabled");
        sendButton.textContent = "Send Page To Analyzer";
        analyseButton.style.display = currentJob ? "block" : "none";
    }

    analyseButton.disabled = false;
    analyseButton.classList.remove("disabled");
    analyseButton.textContent = "Analyse Resume Match";

    if (isBusy) {
        sendButton.disabled = true;
        analyseButton.disabled = true;
    }
}

function sendExtractMessage(tabId) {
    return new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tabId, { action: "extract" }, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
                return;
            }

            if (!response) {
                reject(new Error("No data received from content script"));
                return;
            }

            resolve(response);
        });
    });
}

async function getActiveTab() {
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    return tab;
}

async function getPageData(tab) {
    if (!tab || !tab.id) {
        throw new Error("No active tab found");
    }

    const url = tab.url || "";
    const isSupportedUrl = url.startsWith("http://") || url.startsWith("https://");

    if (!isSupportedUrl) {
        throw new Error("Open a regular website tab (http/https) and try again");
    }

    try {
        return await sendExtractMessage(tab.id);
    } catch (error) {
        if (!error.message.includes("Receiving end does not exist")) {
            throw error;
        }

        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ["content.js"]
        });

        return await sendExtractMessage(tab.id);
    }
}

function extractJobs(payload) {
    if (Array.isArray(payload)) {
        return payload;
    }

    if (!payload || typeof payload !== "object") {
        return [];
    }

    if (Array.isArray(payload.jobs)) {
        return payload.jobs;
    }

    if (Array.isArray(payload.data)) {
        return payload.data;
    }

    return [];
}

function findJobByLink(jobs, link) {
    const targetLink = normalizeJobLink(link);

    return jobs.find((job) => {
        const source = job && typeof job === "object"
            ? (job.job_data && typeof job.job_data === "object" ? job.job_data : job)
            : {};
        const jobLink = normalizeJobLink(source.job_link || source.url || source.link || "");
        return jobLink && jobLink === targetLink;
    }) || null;
}

function extractSavedAnalysis(jobRecord) {
    if (!jobRecord || typeof jobRecord !== "object") {
        return null;
    }

    if (jobRecord.analysis && typeof jobRecord.analysis === "object") {
        const missing = normalizeSkills(jobRecord.analysis.missing_skills);
        return {
            payload: { ...jobRecord.analysis, missing_skills: missing },
            has_missing_skills: missing.length > 0
        };
    }

    if (typeof jobRecord.score === "number") {
        const missing = normalizeSkills(jobRecord.missing_skills);
        return {
            payload: { score: jobRecord.score, missing_skills: missing },
            has_missing_skills: missing.length > 0
        };
    }

    if (typeof jobRecord.analysis_score === "number") {
        const missing = normalizeSkills(jobRecord.missing_skills);
        return {
            payload: { score: jobRecord.analysis_score, missing_skills: missing },
            has_missing_skills: missing.length > 0
        };
    }

    if (typeof jobRecord.matchScore === "number") {
        const missing = normalizeSkills(jobRecord.missing_skills);
        return {
            payload: { score: jobRecord.matchScore, missing_skills: missing },
            has_missing_skills: missing.length > 0
        };
    }

    return null;
}

async function initializePopupState() {
    currentJob = null;
    currentJobId = null;
    activeJobLink = "";
    jobExistsInDatabase = false;
    analysisReady = false;
    document.getElementById("jobDetails").innerHTML = "";
    document.getElementById("analysis").innerHTML = "";
    setVisible("jobDetails", false);
    setVisible("analysis", false);

    const tab = await getActiveTab();
    const currentUrl = normalizeJobLink(tab && tab.url ? tab.url : "");

    activeJobLink = currentUrl;
    updateActionButtons();

    if (!activeJobLink || (!activeJobLink.startsWith("http://") && !activeJobLink.startsWith("https://"))) {
        setStatus("Open a regular website tab to continue.", "warn");
        return;
    }

    await fetchExistingJobForCurrentUrl();
}

async function fetchExistingJobForCurrentUrl() {
    const token = getStoredToken();

    if (!token || !activeJobLink) {
        return;
    }

    try {
        const commonHeaders = {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        };
        const res = await requestWithRouteFallback([
            {
                path: "/get_jobs",
                options: { method: "GET", headers: commonHeaders }
            },
            {
                path: "/get_jobs",
                options: { method: "POST", headers: commonHeaders, body: JSON.stringify({}) }
            },
            {
                path: "/jobs/get_jobs",
                options: { method: "GET", headers: commonHeaders }
            },
            {
                path: "/jobs/get_jobs",
                options: { method: "POST", headers: commonHeaders, body: JSON.stringify({}) }
            }
        ]);

        const { data } = await parseApiResponse(res);

        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem("token");
                showLogin();
            }
            return;
        }

        const jobs = extractJobs(data);
        const existingJob = findJobByLink(jobs, activeJobLink);

        if (!existingJob) {
            setStatus("No saved job found for this page.", "info");
            updateActionButtons();
            return;
        }

        jobExistsInDatabase = true;
        const normalizedJob = normalizeJobPayload(existingJob);
        normalizedJob.job_link = activeJobLink;
        currentJobId = existingJob.id || normalizedJob.id || null;
        displayJob(normalizedJob);
        setStatus("Job already saved for this URL.", "success");

        const savedAnalysis = extractSavedAnalysis(existingJob);
        if (savedAnalysis) {
            renderAnalysisResult(savedAnalysis.payload);
            if (!savedAnalysis.has_missing_skills && currentJobId) {
                await runAnalysis({ silent: true });
            }
        }
    } catch (error) {
        console.error("Failed to fetch jobs:", error);
    }

    updateActionButtons();
}

async function runAnalysis({ silent = false } = {}) {
    setBusyState(true, "Analysing resume match...");
    try {
        const token = getStoredToken();
        if (!token) {
            localStorage.removeItem("token");
            showLogin();
            throw new Error("Session expired. Please login again.");
        }

        if (!currentJobId) {
            await fetchExistingJobForCurrentUrl();
        }

        if (!currentJobId) {
            throw new Error("Job ID not found. Save the page data first.");
        }

        const model = getSelectedModel();
        const body = JSON.stringify({
            model,
            job_id: currentJobId
        });

        console.log("Sending analysis request with payload:", { model, job_id: currentJobId, body });
        const headers = {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        };
        const res = await requestWithRouteFallback([
            {
                path: "/analyze_job",
                options: { method: "POST", headers, body }
            },
        ]);

        const { data: result } = await parseApiResponse(res);

        if (res.status === 401) {
            localStorage.removeItem("token");
            showLogin();
            throw new Error("Unauthorized (401). Please login again.");
        }

        if (!res.ok) {
            throw new Error(getApiError(res, result, "Analysis failed"));
        }

        if (!result || typeof result !== "object") {
            throw new Error("Invalid response from analyze_job");
        }

        renderAnalysisResult(result);
        if (!silent) {
            setStatus("Analysis completed.", "success");
        }
    } finally {
        setBusyState(false);
    }
}

async function saveCurrentJob({ silent = false } = {}) {
    const token = getStoredToken();
    const model = getSelectedModel();

    if (!currentJob) {
        throw new Error("No job details to save");
    }

    if (!token) {
        throw new Error("Session expired. Please login again.");
    }

    const payload = {
        ...currentJob,
        job_link: activeJobLink || currentJob.job_link || "",
        model,
        progress: "Checking"
    };

    console.log("Saving job payload:", payload);

    const res = await fetch(`${API}/save_job`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });

    const { data } = await parseApiResponse(res);

    if (res.status === 401) {
        localStorage.removeItem("token");
        showLogin();
        throw new Error("Unauthorized (401). Please login again.");
    }

    if (!res.ok) {
        throw new Error(getApiError(res, data, "Error saving job"));
    }

    jobExistsInDatabase = true;
    currentJobId = (data && (data.job_id || data.id)) || currentJobId;
    updateActionButtons();

    if (!silent) {
        setStatus("Job saved successfully.", "success");
    }

    return data;
}

document.getElementById("modelSelect").onchange = (event) => {
    localStorage.setItem(MODEL_STORAGE_KEY, event.target.value || "");
};

document.getElementById("loginBtn").onclick = async () => {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    document.getElementById("loginError").innerText = "";

    try {
        const res = await fetch(`${API}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const { data } = await parseApiResponse(res);
        const token = extractAuthToken(data);

        if (res.ok && token) {
            localStorage.setItem("token", token);
            showApp();
        } else {
            document.getElementById("loginError").innerText =
                (data && data.error) || getApiError(res, data, "Login failed");
        }
    } catch (error) {
        document.getElementById("loginError").innerText =
            error.message || "Login failed";
    }
};

document.getElementById("send").onclick = async () => {
    if (isBusy) {
        return;
    }

    const loading = document.getElementById("loading");
    loading.innerText = "Parsing job description...";
    loading.style.display = "block";
    clearStatus();
    setBusyState(true, "Parsing job description...");

    try {
        const tab = await getActiveTab();
        const data = await getPageData(tab);
        const model = getSelectedModel();

        activeJobLink = normalizeJobLink(data.url || tab.url || "");

        const parsePayload = {
            job_description: data.text || "",
            job_link: activeJobLink,
            model,
            progress: "Checking"
        };

        console.log("Sending payload to parse_jd_txt:", parsePayload);

        const res = await fetch(`${API}/parse_jd_txt`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(parsePayload)
        });

        const { data: jobPayload } = await parseApiResponse(res);
        console.log("API response for job details:", jobPayload);

        if (!res.ok) {
            throw new Error(getApiError(res, jobPayload, "Failed to parse job details"));
        }

        if (!jobPayload || typeof jobPayload !== "object") {
            throw new Error("Invalid response from parse_jd_txt");
        }

        const job = normalizeJobPayload(jobPayload);
        job.job_link = activeJobLink;
        job.progress = "Checking";
        analysisReady = false;
        displayJob(job);

        const filledCount = countFilledCoreFields(job);
        if (filledCount > 3) {
            await saveCurrentJob({ silent: true });
            await fetchExistingJobForCurrentUrl();
            setStatus("Page parsed and auto-saved.", "success");
        } else {
            setStatus("Page parsed. Waiting for more complete fields before auto-save.", "warn");
            updateActionButtons();
        }
        setBusyState(false);
    } catch (error) {
        loading.innerText = error.message;
        console.error("Send flow failed:", error);
        setBusyState(false);
    }
};

document.getElementById("analyse").onclick = async () => {
    try {
        if (isBusy) {
            return;
        }
        if (analysisReady) {
            return;
        }
        await runAnalysis();
    } catch (error) {
        document.getElementById("analysis").innerText =
            error.message || "Analysis failed";
        setVisible("analysis", true);
    }
};

document.getElementById("logout").onclick = () => {
    localStorage.removeItem("token");
    showLogin();
};
