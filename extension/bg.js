// background.js

let currentTabId = null;

// Listen for tab activation (focus change within window)
chrome.tabs.onActivated.addListener(activeInfo => {
    currentTabId = activeInfo.tabId;
    console.log("Tab activated:", currentTabId);
    requestMetadataFromTab(currentTabId);
});

// Listen for window focus change (focus change between windows)
chrome.windows.onFocusChanged.addListener(windowId => {
    if (windowId === chrome.windows.WINDOW_ID_NONE) return;

    chrome.tabs.query({ active: true, windowId: windowId }, tabs => {
        if (tabs && tabs.length > 0) {
            const newTabId = tabs[0].id;
            console.log("Window focused, tab:", newTabId);
            currentTabId = newTabId;
            requestMetadataFromTab(newTabId);
        }
    });
});

// Also listen for updates (page load complete)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tabId === currentTabId) {
        requestMetadataFromTab(tabId);
    }
});

function requestMetadataFromTab(tabId) {
    if (!tabId) return;

    chrome.tabs.get(tabId, (tab) => {
        if (chrome.runtime.lastError || !tab) return;

        // Check if allowed domain
        const url = tab.url || "";
        const isAllowed = url.includes("samsung.net") ||
            url.includes("sec.samsung.net") ||
            url.startsWith("file:///") ||
            url.includes("127.0.0.1") ||
            url.includes("localhost");

        if (!isAllowed) {
            console.log("Ignored domain (Not PLM/Local):", url);
            // We NO LONGER tell the app to clear context if it's a completely foreign domain
            // This prevents the status bar from showing 'Active' on Google.
            return;
        }

        // It's an allowed domain, ask the content script for metadata
        chrome.tabs.sendMessage(tabId, { action: "get_metadata" }, (response) => {
            if (chrome.runtime.lastError) {
                // Content script might not be injected yet or not a PLM page
                console.log("Allowed page but no content script responder. Clearing.");
                sendToLocalApp({ defect_id: "", plm_id: "", title: "", url: tab.url });
                return;
            }

            if (response) {
                console.log("Got metadata:", response);
                sendToLocalApp(response);
            }
        });
    });
}

// Dynamic Port Config
let currentPort = 5555;
const START_PORT = 5555;
const END_PORT = 5564;

async function sendToLocalApp(data) {
    // 1. Try Primary (Network)
    let success = await trySend(currentPort, data);
    if (success) {
        return;
    }

    // 2. Scan ports if first attempt failed
    console.log(`Port ${currentPort} failed. Scanning for active server...`);
    const foundPort = await scanForPort();

    if (foundPort) {
        currentPort = foundPort;
        console.log(`Discovered active server on port ${currentPort}`);
        await trySend(currentPort, data);
    } else {
        // Ghost Title Bridge (in content.js) will handle the sync silently
        console.warn("Network blocked. Relying on Ghost Title Bridge.");
    }
}

async function trySend(port, data) {
    try {
        const response = await fetch(`http://127.0.0.1:${port}/update_context`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function scanForPort() {
    for (let p = START_PORT; p <= END_PORT; p++) {
        const isAlive = await checkHealth(p);
        if (isAlive) return p;
    }
    return null;
}

async function checkHealth(port) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 200); // Fast timeout

        const response = await fetch(`http://127.0.0.1:${port}/health`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response.ok;
    } catch (error) {
        return false;
    }
}
