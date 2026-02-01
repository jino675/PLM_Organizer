// PLM Organizer Helper - Background Script (v1.7.1 GHOST ONLY)
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
            log("Ignored domain (Not PLM/Local). Stay silent.");
            return;
        }

        log("Sending 'get_metadata' message to content script...");
        // It's an allowed domain, ask the content script for metadata
        // Note: We don't do anything with the response here anymore.
        // The content script will update the Window Title, which the App (Ghost Bridge) watches.
        chrome.tabs.sendMessage(tabId, { action: "get_metadata" }, (response) => {
            if (chrome.runtime.lastError) {
                log("Message FAIL (Content script not ready or error):", chrome.runtime.lastError.message);
                return;
            }
            log("Message SUCCESS. Triggered Ghost Bridge update.");
        });
    });
}
