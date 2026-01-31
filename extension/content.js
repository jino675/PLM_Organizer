// --- Configuration Section (Optimization Ready) ---
const CONFIG = {
    selectors: {
        plmId: '#content > div:nth-child(1) > table > tbody > tr > th:nth-child(1) > strong, #plm-id-value',
        defectId: '#content > div.dataGrid.nolist.mgT-1 > table > tbody > tr:nth-child(19) > td > table > tbody > tr > td > a, #kona-id-value',
        title: '#content > div:nth-child(1) > table > tbody > tr > th:nth-child(2), #plm-title'
    },
    anchors: {
        defect: ["KONA ID", "결함 ID", "Defect ID"],
        plm: ["PLM ID", "등록번호", "ID"],
        title: ["Title", "제목", "Subject"]
    }
};

// --- Ghost Title Bridge (No-Network Sync) ---
let originalTitle = document.title;
let lastMetadataTag = "";

function syncTitle(metadata) {
    if (!metadata.defect_id && !metadata.plm_id) return;

    const id = (metadata.defect_id || metadata.plm_id || "").substring(0, 30);
    // User Requirement: Send RAW title. 
    // Only escape structural characters that break the tag syntax (| and ]).
    // Using distinct symbols (‖, ⦗, ⦘) that the App will restore.
    const rawTitle = (metadata.title || "Untitled")
        .replace(/\|/g, "‖")
        .replace(/\[/g, "⦗")
        .replace(/\]/g, "⦘")
        .substring(0, 200);

    const tag = `[PLM_CTX:${id}|${rawTitle}]`;

    if (tag === lastMetadataTag) return;
    lastMetadataTag = tag;

    console.log("Ghost Syncing:", tag);
    document.title = tag + " " + originalTitle;

    setTimeout(() => {
        document.title = originalTitle;
    }, 2000);
}

// Watch for manual title changes to keep 'originalTitle' fresh
const titleObserver = new MutationObserver(() => {
    const newTitle = document.title;
    if (!newTitle.includes("[PLM_CTX:")) {
        originalTitle = newTitle;
    }
});
const titleNode = document.querySelector('title');
if (titleNode) titleObserver.observe(titleNode, { childList: true });

function findValueByAnchor(keywords) {
    const elements = document.querySelectorAll('th, td, label, span, .label');
    for (let el of elements) {
        const text = el.innerText.trim();
        if (keywords.some(k => text === k || text.includes(k + ":"))) {
            let next = el.nextElementSibling;
            if (next && next.innerText.trim()) return next.innerText.trim();
            let parentNext = el.parentElement?.nextElementSibling;
            if (parentNext && parentNext.innerText.trim()) return parentNext.innerText.trim();
        }
    }
    return "";
}

function parseMetadata() {
    let defectId = "";
    let plmId = "";
    let title = "";

    const elDefect = document.querySelector(CONFIG.selectors.defectId);
    if (elDefect) defectId = elDefect.innerText.trim();

    const elPlm = document.querySelector(CONFIG.selectors.plmId);
    if (elPlm) plmId = elPlm.innerText.trim();

    const elTitle = document.querySelector(CONFIG.selectors.title);
    if (elTitle) title = elTitle.innerText.trim();

    if (!defectId) defectId = findValueByAnchor(CONFIG.anchors.defect);
    if (!plmId) plmId = findValueByAnchor(CONFIG.anchors.plm);

    if (!title) {
        const h = document.querySelector('h1, h2, .page-title, .title');
        if (h) title = h.innerText.trim();
    }

    if (!plmId && !defectId) {
        const pMatch = document.body.innerText.match(/P\d{6}-\d{5}/);
        if (pMatch) plmId = pMatch[0];
    }

    const data = {
        defect_id: defectId,
        plm_id: plmId,
        title: title,
        url: window.location.href
    };

    if (data.defect_id || data.plm_id) {
        syncTitle(data);
    }

    return data;
}

// Auto-Sync Setup
setTimeout(parseMetadata, 1000);
let debounceTimer;
const bodyObserver = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(parseMetadata, 1000);
});
bodyObserver.observe(document.body, { childList: true, subtree: true });

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_metadata") {
        const data = parseMetadata();
        sendResponse(data);
    }
});
