// content.js
console.log("PLM Organizer Content Script Loaded");

// --- Ghost Title Bridge (No-Network Sync) ---
let originalTitle = document.title;
let lastMetadataTag = "";

function syncTitle(metadata) {
    if (!metadata.defect_id && !metadata.plm_id) return;

    const id = metadata.defect_id || metadata.plm_id;
    const cleanTitle = (metadata.title || "Untitled").replace(/[\[\]]/g, "").trim();
    const tag = `[PLM_CTX:${id}|${cleanTitle}]`;

    if (tag === lastMetadataTag) return;
    lastMetadataTag = tag;

    console.log("Ghost Syncing:", tag);
    document.title = tag + " " + originalTitle;

    setTimeout(() => {
        document.title = originalTitle;
    }, 2000);
}

const titleObserver = new MutationObserver(() => {
    const newTitle = document.title;
    if (!newTitle.includes("[PLM_CTX:")) {
        originalTitle = newTitle;
    }
});
const titleNode = document.querySelector('title');
if (titleNode) titleObserver.observe(titleNode, { childList: true });

function parseMetadata() {
    let defectId = "";
    let plmId = "";
    let title = "";

    // 1. Check for specific Mock IDs first
    const mockDefect = document.getElementById('kona-id-value');
    if (mockDefect && mockDefect.innerText.trim()) defectId = mockDefect.innerText.trim();
    const mockPlm = document.getElementById('plm-id-value');
    if (mockPlm && mockPlm.innerText.trim()) plmId = mockPlm.innerText.trim();
    const mockTitle = document.getElementById('plm-title');
    if (mockTitle && mockTitle.innerText.trim()) title = mockTitle.innerText.trim();

    // 2. Generic Search (Real PLM or fallback)
    if (!defectId) {
        const labels = document.querySelectorAll('.label, span, div, th, td');
        for (let el of labels) {
            if (el.innerText && el.innerText.includes("KONA ID")) {
                let next = el.nextElementSibling;
                if (next && next.innerText.trim()) {
                    defectId = next.innerText.trim();
                    break;
                }
            }
        }
    }

    if (!plmId) {
        const pMatch = document.body.innerText.match(/P\d{5,6}-\d{4,5}/);
        if (pMatch) plmId = pMatch[0];
    }
    if (!title) {
        const h2 = document.querySelector('h2');
        if (h2) title = h2.innerText.trim();
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

// 1. Auto-Parse on Load (Wait for page scripts)
setTimeout(parseMetadata, 1000);

// 2. Auto-Parse on DOM Changes (Dynamic Pages)
let debounceTimer;
const bodyObserver = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(parseMetadata, 1000);
});
bodyObserver.observe(document.body, { childList: true, subtree: true });

// 3. Listen for Background requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_metadata") {
        const data = parseMetadata();
        sendResponse(data);
    }
});
