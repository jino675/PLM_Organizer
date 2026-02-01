// PLM Organizer Helper - Background Script (v1.6.9 DEBUG)
let currentTabId = null;

// [DEBUG] Logging wrapper
function log(msg, ...args) {
    console.log(`[BG] ${msg}`, ...args);
}

// Listen for tab activation (focus change within window)
chrome.tabs.onActivated.addListener(activeInfo => {
    currentTabId = activeInfo.tabId;
    log("Tab ACTIVATED. ID:", currentTabId);
    requestMetadataFromTab(currentTabId);
});

// Listen for window focus change (focus change between windows)
chrome.windows.onFocusChanged.addListener(windowId => {
    if (windowId === chrome.windows.WINDOW_ID_NONE) {
        log("Window Focus LOST (None)");
        return;
    }

    log("Window Focus CHANGED to Window ID:", windowId);
    chrome.tabs.query({ active: true, windowId: windowId }, tabs => {
        if (chrome.runtime.lastError || !tabs || tabs.length === 0) {
            log("Error querying active tab in window:", chrome.runtime.lastError);
            return;
        }
        const newTabId = tabs[0].id;
        log("New Active Tab in Window:", newTabId);
        currentTabId = newTabId;
        requestMetadataFromTab(newTabId);
    });
});

// Also listen for updates (page load complete)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tabId === currentTabId) {
        log("Current Tab UPDATED (Page Load Complete). ID:", tabId);
        requestMetadataFromTab(tabId);
    }
});

function requestMetadataFromTab(tabId) {
    if (!tabId) {
        log("Skipping request: No Tab ID");
        return;
    }

    chrome.tabs.get(tabId, (tab) => {
        if (chrome.runtime.lastError || !tab) {
            log("Error getting tab details:", chrome.runtime.lastError);
            return;
        }

        // Check if allowed domain - Synchronization with manifest.json
        const url = tab.url || "";
        const isAllowed = url.includes("splm.sec.samsung.net") ||
            url.startsWith("file:///") ||
            url.includes("127.0.0.1") ||
            url.includes("localhost");

        log(`Checking permissions for URL: ${url.substring(0, 50)}... -> Allowed? ${isAllowed}`);

        if (!isAllowed) {
            log("Ignored domain (Not PLM/Local). Context kept as-is.");
            // STABLE CONTEXT: Do NOT clear context here. 
            // This keeps the last PLM info active when switching to regular tabs.
            return;
        }

        log("Sending 'get_metadata' message to content script...");
        // It's an allowed domain, ask the content script for metadata
        chrome.tabs.sendMessage(tabId, { action: "get_metadata" }, (response) => {
            if (chrome.runtime.lastError) {
                // Content script might not be injected yet or temporary error.
                // WE DO NOT CLEAR CONTEXT HERE. Keep the last known state.
                log("Message FAIL (Content script not ready or error):", chrome.runtime.lastError.message);
                return;
            }

            if (response) {
                log("Message SUCCESS. Got metadata:", response);
                sendToLocalApp(response);
            } else {
                log("Message SUCCESS but empty response.");
            }
        });
    });
}

function sendToLocalApp(data) {
    const ports = [5555, 5556, 5557, 5558, 5559, 5560, 5561, 5562, 5563, 5564];

    const tryPort = (index) => {
        if (index >= ports.length) {
            log("Local server not found on ANY port. Gave up.");
            return;
        }

        const port = ports[index];
        // log(`Trying to send to localhost:${port}...`); // Too verbose?
        fetch(`http://127.0.0.1:${port}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(() => log(`Data successfully SENT to local app on port ${port}`))
            .catch(() => tryPort(index + 1));
    };

    tryPort(0);
}
