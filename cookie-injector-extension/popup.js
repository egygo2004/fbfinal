document.getElementById('inject').addEventListener('click', async () => {
    const url = document.getElementById('url').value.trim();
    const cookiesJson = document.getElementById('cookies').value.trim();
    const statusEl = document.getElementById('status');

    // Reset status
    statusEl.className = 'status';
    statusEl.style.display = 'none';

    // Validate inputs
    if (!url) {
        showStatus('Please enter a URL', 'error');
        return;
    }

    if (!cookiesJson) {
        showStatus('Please enter cookies JSON', 'error');
        return;
    }

    // Parse cookies
    let cookies;
    try {
        cookies = JSON.parse(cookiesJson);
        if (!Array.isArray(cookies)) {
            throw new Error('Cookies must be an array');
        }
    } catch (e) {
        showStatus('Invalid JSON: ' + e.message, 'error');
        return;
    }

    // Disable button
    const btn = document.getElementById('inject');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Injecting...';

    try {
        // Set each cookie
        let successCount = 0;
        for (const cookie of cookies) {
            try {
                // Convert sameSite to valid Chrome values
                let sameSiteValue = 'lax'; // default
                if (cookie.sameSite) {
                    const siteVal = cookie.sameSite.toLowerCase();
                    if (siteVal === 'strict') sameSiteValue = 'strict';
                    else if (siteVal === 'none' || siteVal === 'no_restriction') sameSiteValue = 'no_restriction';
                    else if (siteVal === 'lax') sameSiteValue = 'lax';
                    else sameSiteValue = 'unspecified';
                }

                // Build cookie object for Chrome API
                const cookieDetails = {
                    url: 'https://www.facebook.com',
                    name: cookie.name,
                    value: cookie.value,
                    domain: cookie.domain || '.facebook.com',
                    path: cookie.path || '/',
                    secure: cookie.secure !== false,
                    httpOnly: cookie.httpOnly || false,
                    sameSite: sameSiteValue
                };

                // Add expiry if present
                if (cookie.expiry) {
                    cookieDetails.expirationDate = cookie.expiry;
                } else if (cookie.expirationDate) {
                    cookieDetails.expirationDate = cookie.expirationDate;
                } else {
                    // Set expiry to 1 year from now
                    cookieDetails.expirationDate = Math.floor(Date.now() / 1000) + 31536000;
                }

                await chrome.cookies.set(cookieDetails);
                successCount++;
            } catch (cookieError) {
                console.warn('Failed to set cookie:', cookie.name, cookieError);
            }
        }

        showStatus(`✅ Injected ${successCount}/${cookies.length} cookies. Opening URL...`, 'success');

        // Open URL in new tab
        setTimeout(() => {
            chrome.tabs.create({ url: url });
        }, 500);

    } catch (e) {
        showStatus('Error: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🚀</span> Inject & Open';
    }
});

function showStatus(message, type) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = 'status ' + type;
}

// Load saved values on popup open
document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.local.get(['lastUrl', 'lastCookies'], (result) => {
        if (result.lastUrl) {
            document.getElementById('url').value = result.lastUrl;
        }
        if (result.lastCookies) {
            document.getElementById('cookies').value = result.lastCookies;
        }
    });
});

// Save values when typing
document.getElementById('url').addEventListener('input', (e) => {
    chrome.storage.local.set({ lastUrl: e.target.value });
});

document.getElementById('cookies').addEventListener('input', (e) => {
    chrome.storage.local.set({ lastCookies: e.target.value });
});
