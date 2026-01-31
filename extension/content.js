// content.js
console.log("PLM Organizer Content Script Loaded");

// --- Ghost Title Bridge (No-Network Sync) ---
let originalTitle = document.title;
let lastMetadataTag = "";

function syncTitle(metadata) {
    if (!metadata.defect_id && !metadata.plm_id) return;

    const id = metadata.defect_id || metadata.plm_id;
    const cleanTitle = (metadata.title || "Untitled").replace(/[\[\]]/g, ""); // Remove brackets from title
    const tag = `[PLM_CTX:${id}|${cleanTitle}]`;

    if (tag === lastMetadataTag) return;
    lastMetadataTag = tag;

    // Temporarily inject tag into title
    // Format: [PLM_CTX:ID|Title] Real Page Title
    document.title = tag + " " + originalTitle;

    // Optional: Revert after 2 seconds to keep it clean, 
    // but keep it long enough for the Python app to catch it.
    setTimeout(() => {
        document.title = originalTitle;
    }, 2000);
}

// Watch for manual title changes by the page itself
const titleObserver = new MutationObserver((mutations) => {
    const newTitle = document.title;
    if (!newTitle.includes("[PLM_CTX:")) {
        originalTitle = newTitle;
    }
});
titleObserver.observe(document.querySelector('title'), { childList: true });

function parseMetadata() {
    let defectId = "";
    let plmId = "";
    let title = "";

    // 1. Parse Defect ID (near "KONA ID")
    const labels = document.querySelectorAll('.label, span, div, th, td');
    for (let el of labels) {
        if (el.innerText && el.innerText.includes("KONA ID")) {
            let next = el.nextElementSibling;
            if (next && next.innerText) {
                defectId = next.innerText.trim();
                break;
            }
            if (el.tagName === 'TD' || el.tagName === 'TH') {
                let nextCell = el.nextElementSibling;
                if (nextCell) {
                    defectId = nextCell.innerText.trim();
                    break;
                }
            }
        }
    }

    // Explicit Mock Support
    const mockDefect = document.getElementById('kona-id-value');
    if (mockDefect) defectId = mockDefect.innerText.trim();
    const mockPlm = document.getElementById('plm-id-value');
    if (mockPlm) plmId = mockPlm.innerText.trim();
    const mockTitle = document.getElementById('plm-title');
    if (mockTitle) title = mockTitle.innerText.trim();

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

    // Sync to Title (Ghost Bridge)
    syncTitle(data);

    return data;
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_metadata") {
        const data = parseMetadata();
        sendResponse(data);
    }
});
