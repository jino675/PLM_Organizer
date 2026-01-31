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

        // Check if allowed domain
        const url = tab.url || "";
        const isAllowed = url.includes("splm.sec.samsung.net") || url.startsWith("file:///");

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

async function sendToLocalApp(data) {
    let success = await trySend(currentPort, data);
    if (success) return;

    // If failed, scan for new port
    console.log(`Port ${currentPort} failed. Scanning for active server...`);
    const foundPort = await scanForPort();

    if (foundPort) {
        currentPort = foundPort;
        console.log(`Discovered active server on port ${currentPort}`);
        // Retry sending to the new port
        await trySend(currentPort, data);
    } else {
        console.error("Could not find PLM Organizer server on ports 5555-5564.");
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
