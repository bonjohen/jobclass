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
