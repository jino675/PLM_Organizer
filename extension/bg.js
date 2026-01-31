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
            currentTabId = tabs[0].id;
            console.log("Window focused, tab:", currentTabId);
            requestMetadataFromTab(currentTabId);
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

        // Check if allowed domain (broadened for Samsung intranet)
        const url = tab.url || "";
        const isAllowed = url.includes("samsung.net") || url.includes("sec.samsung.net") || url.startsWith("file:///");

        if (!isAllowed) {
            console.log("Non-PLM page focused:", url, "Clearing context.");
            sendToLocalApp({ defect_id: "", plm_id: "", title: "", url: url });
            return;
        }

        // It's an allowed domain, ask the content script for metadata
        chrome.tabs.sendMessage(tabId, { action: "get_metadata" }, (response) => {
            if (chrome.runtime.lastError) {
                // Should not happen if manifest is correct, but safety first
                console.log("Allowed page but no content script. Clearing context.");
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

// Track last sent data to avoid redundant Ninja Mode downloads
let lastSentData = null;

async function sendToLocalApp(data) {
    // 1. Try Primary (Network)
    let success = await trySend(currentPort, data);
    if (success) {
        lastSentData = JSON.stringify(data);
        return;
    }

    // 2. Scan ports if first attempt failed
    console.log(`Port ${currentPort} failed. Scanning for active server...`);
    const foundPort = await scanForPort();

    if (foundPort) {
        currentPort = foundPort;
        console.log(`Discovered active server on port ${currentPort}`);
        success = await trySend(currentPort, data);
        if (success) {
            lastSentData = JSON.stringify(data);
            return;
        }
    }

    // 3. Last Resort: Ninja Mode (File-based Bridge)
    // Only download if data has changed to avoid spamming downloads
    const dataStr = JSON.stringify(data);
    if (dataStr !== lastSentData) {
        console.warn("Network 100% blocked. Using Ninja Mode (File Bridge)...");
        saveToFileBridge(data);
        lastSentData = dataStr;
    }
}

function saveToFileBridge(data) {
    const json = JSON.stringify(data);
    const blob = new Blob([json], { type: "application/json" });
    const reader = new FileReader();

    reader.onload = function () {
        chrome.downloads.download({
            url: reader.result,
            filename: "_plm_context.json",
            conflictAction: "overwrite",
            saveAs: false
        }, (downloadId) => {
            if (chrome.runtime.lastError) {
                console.error("Ninja Mode Failed:", chrome.runtime.lastError.message);
            } else {
                console.log("Ninja Mode: Metadata file sent to Downloads folder.", downloadId);
            }
        });
    };
    reader.readAsDataURL(blob);
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
