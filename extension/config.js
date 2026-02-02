// PLM Organizer Helper - Shared Configuration (v1.8.14)
const SHARED_CONFIG = {
    // 🔒 Security: Only run on these domains/patterns.
    // Unifies logic between Background (bg.js) and Content (content.js) scripts.
    ALLOWED_PATTERNS: [
        "splm.sec.samsung.net",
        "file:///",
        "127.0.0.1",
        "localhost"
    ]
};

/**
 * Checks if a given string URL matches any of the allowed patterns.
 * @param {string} url - The full URL to check.
 * @returns {boolean}
 */
function isUrlAllowed(url) {
    if (!url) return false;
    return SHARED_CONFIG.ALLOWED_PATTERNS.some(pattern => url.includes(pattern));
}
