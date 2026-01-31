// PLM Organizer Helper - Background Script
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
        if (chrome.runtime.lastError || !tabs || tabs.length === 0) return;
        const newTabId = tabs[0].id;
        console.log("Window focused, tab:", newTabId);
        currentTabId = newTabId;
        requestMetadataFromTab(newTabId);
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

        // Check if allowed domain - Synchronization with manifest.json
        const url = tab.url || "";
        const isAllowed = url.includes("splm.sec.samsung.net") ||
            url.startsWith("file:///") ||
            url.includes("127.0.0.1") ||
            url.includes("localhost");

        if (!isAllowed) {
            console.log("Ignored domain (Not PLM/Local):", url);
            // STABLE CONTEXT: Do NOT clear context here. 
            // This keeps the last PLM info active when switching to regular tabs.
            return;
        }

        // It's an allowed domain, ask the content script for metadata
        chrome.tabs.sendMessage(tabId, { action: "get_metadata" }, (response) => {
            if (chrome.runtime.lastError) {
                // Content script might not be injected yet or temporary error.
                // WE DO NOT CLEAR CONTEXT HERE. Keep the last known state.
                console.log("Allowed page but messaging error. Keeping existing context.");
                return;
            }

            if (response) {
                console.log("Got metadata:", response);
                sendToLocalApp(response);
            }
        });
    });
}

function sendToLocalApp(data) {
    const ports = [5555, 5556, 5557, 5558, 5559, 5560, 5561, 5562, 5563, 5564];

    const tryPort = (index) => {
        if (index >= ports.length) {
            console.log("Local server not found on any port. Using Ghost Title Bridge only.");
            return;
        }

        const port = ports[index];
        fetch(`http://127.0.0.1:${port}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(() => console.log(`Data sent to local app on port ${port}`))
            .catch(() => tryPort(index + 1));
    };

    tryPort(0);
}
