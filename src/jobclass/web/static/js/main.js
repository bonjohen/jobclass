/* JobClass — Main JavaScript */

"use strict";

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
