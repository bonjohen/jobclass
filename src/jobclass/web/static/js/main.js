/* JobClass — Main JavaScript */

"use strict";

/** Default timeout for API fetch calls (milliseconds). */
var FETCH_TIMEOUT_MS = 10000;

/**
 * Fetch with an automatic abort timeout.
 * Returns a Promise that rejects with AbortError if the timeout elapses.
 */
function fetchWithTimeout(url, timeoutMs) {
    var ms = timeoutMs || FETCH_TIMEOUT_MS;
    var controller = new AbortController();
    var timer = setTimeout(function() { controller.abort(); }, ms);
    return fetch(url, { signal: controller.signal }).finally(function() { clearTimeout(timer); });
}

/**
 * Format a number with thousand separators.
 * Returns "N/A" for null/undefined values.
 */
function formatNumber(value) {
    if (value == null) return "N/A";
    return Number(value).toLocaleString("en-US");
}

/**
 * Format a currency value (USD).
 * Returns "N/A" for null/undefined (suppressed) values.
 */
function formatWage(value) {
    if (value == null) return "N/A";
    return "$" + Number(value).toLocaleString("en-US", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    });
}

/**
 * Format a percentage value.
 * Returns "N/A" for null/undefined values.
 */
function formatPercent(value) {
    if (value == null) return "N/A";
    return Number(value).toFixed(1) + "%";
}

/**
 * Escape a string for safe insertion into HTML.
 * Returns empty string for null/undefined.
 */
function escapeHtml(text) {
    if (text == null) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
}

/**
 * Escape a value for safe use in an HTML attribute (e.g., href).
 * Returns empty string for null/undefined.
 */
function escapeAttr(value) {
    if (value == null) return "";
    return String(value).replace(/&/g, "&amp;").replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* --- Theme Toggle --- */

(function() {
    var THEME_KEY = 'jobclass:theme';
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function() {
        var cur = document.documentElement.getAttribute('data-theme');
        var next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem(THEME_KEY, next);
    });
})();

/* --- Lesson Category Filter --- */

(function() {
    var btns = document.querySelectorAll('.lesson-filter-btn');
    if (!btns.length) return;
    btns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            btns.forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            var cat = btn.getAttribute('data-cat');
            document.querySelectorAll('.lesson-card').forEach(function(card) {
                card.style.display = (cat === 'all' || card.getAttribute('data-cat') === cat) ? '' : 'none';
            });
        });
    });

    /* --- Hash scroll-to + highlight animation --- */
    var hash = window.location.hash;
    if (hash && hash.length > 1) {
        var target = document.getElementById(hash.substring(1));
        if (target && target.classList.contains('lesson-card')) {
            /* Reset filter to "All" so target card is visible */
            btns.forEach(function(b) { b.classList.toggle('active', b.getAttribute('data-cat') === 'all'); });
            document.querySelectorAll('.lesson-card').forEach(function(c) { c.style.display = ''; });

            setTimeout(function() {
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                target.classList.add('lesson-card-highlight');
                setTimeout(function() {
                    target.classList.remove('lesson-card-highlight');
                }, 2200);
            }, 300);
        }
    }
})();
