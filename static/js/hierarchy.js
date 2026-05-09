/* JobClass — Hierarchy page */
"use strict";

(function() {
    var treeDiv = document.getElementById("hierarchy-tree");

    fetchWithTimeout("/api/occupations/hierarchy")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (!data.hierarchy || data.hierarchy.length === 0) {
                treeDiv.innerHTML = '<p>No hierarchy data available.</p>';
                return;
            }
            treeDiv.innerHTML = buildTree(data.hierarchy);
            treeDiv.addEventListener("click", function(e) {
                var toggle = e.target.closest(".tree-toggle");
                if (toggle) {
                    toggleNode(toggle);
                }
            });
            // Keyboard navigation
            treeDiv.addEventListener("keydown", function(e) {
                var toggle = e.target.closest(".tree-toggle");
                if (!toggle) return;
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    toggleNode(toggle);
                } else if (e.key === "ArrowDown") {
                    e.preventDefault();
                    focusNextTreeItem(toggle, 1);
                } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    focusNextTreeItem(toggle, -1);
                } else if (e.key === "ArrowRight") {
                    e.preventDefault();
                    var li = toggle.closest("li");
                    if (li.classList.contains("collapsed")) {
                        toggleNode(toggle);
                    }
                } else if (e.key === "ArrowLeft") {
                    e.preventDefault();
                    var li = toggle.closest("li");
                    if (!li.classList.contains("collapsed")) {
                        toggleNode(toggle);
                    }
                }
            });
        })
        .catch(function() {
            treeDiv.innerHTML = '<p class="error-message">Failed to load hierarchy. Please try again later.</p>';
        });

    function toggleNode(toggle) {
        var li = toggle.closest("li");
        li.classList.toggle("collapsed");
        toggle.setAttribute("aria-expanded",
            li.classList.contains("collapsed") ? "false" : "true");
    }

    function focusNextTreeItem(current, direction) {
        var items = Array.prototype.slice.call(treeDiv.querySelectorAll(".tree-toggle, .tree-link"));
        var idx = items.indexOf(current);
        if (idx === -1) return;
        var next = idx + direction;
        if (next >= 0 && next < items.length) {
            items[next].focus();
        }
    }

    function buildTree(nodes) {
        if (!nodes || nodes.length === 0) return "";
        var html = '<ul class="tree-list" role="group">';
        nodes.forEach(function(n) {
            var hasChildren = n.children && n.children.length > 0;
            html += '<li role="treeitem" class="tree-node' + (hasChildren ? '' : ' leaf') + '">';
            if (hasChildren) {
                html += '<button class="tree-toggle" aria-expanded="true" aria-label="Toggle ' + escapeHtml(n.occupation_title) + '">';
                html += '<span class="toggle-icon">&#9660;</span>';
                html += '</button>';
            } else {
                html += '<span class="tree-spacer"></span>';
            }
            html += '<a href="/occupation/' + escapeAttr(n.soc_code) + '" class="tree-link">';
            html += '<span class="tree-code">' + escapeHtml(n.soc_code) + '</span> ';
            html += '<span class="tree-title">' + escapeHtml(n.occupation_title) + '</span>';
            html += '</a>';
            if (hasChildren) {
                html += buildTree(n.children);
            }
            html += '</li>';
        });
        html += '</ul>';
        return html;
    }

})();
