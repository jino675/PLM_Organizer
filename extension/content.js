// content.js
console.log("PLM Organizer Content Script Loaded");

function parseMetadata() {
    let defectId = "";
    let plmId = "";
    let title = "";

    // 1. Parse Defect ID (near "KONA ID")
    // Strategy: Find label contain "KONA ID", then look for value
    const labels = document.querySelectorAll('.label, span, div, th, td');
    // This is broad, but necessary without specific class names from real DOM.
    // Optimization: Look for text checks.

    for (let el of labels) {
        if (el.innerText && el.innerText.includes("KONA ID")) {
            // Assume the value is in the next sibling or a child of a sibling
            // Or if it's a table, next cell.
            // Using logic from Mock: <span class="value" id="kona-id-value">...</span>

            // Try 1: Next Element Sibling
            let next = el.nextElementSibling;
            if (next && next.innerText) {
                defectId = next.innerText.trim();
                break;
            }

            // Try 2: Next Sibling (Text Node)

            // Try 3: If Table, next cell
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

    // 2. Parse PLM ID (near Title)
    // If not found in mock logic above:
    if (!plmId) {
        // Search for PXXXXX pattern? Or label "PLM ID"
        // Let's search text context for P followed by numbers
        const pMatch = document.body.innerText.match(/P\d{5,6}-\d{4,5}/);
        if (pMatch) plmId = pMatch[0];
    }

    // 3. Parse Title
    if (!title) {
        // Headers?
        const h2 = document.querySelector('h2');
        if (h2) title = h2.innerText.trim();
    }

    return {
        defect_id: defectId,
        plm_id: plmId,
        title: title,
        url: window.location.href
    };
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_metadata") {
        const data = parseMetadata();
        sendResponse(data);
    }
});
