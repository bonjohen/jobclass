/* JobClass — Hierarchy page */
"use strict";

(function() {
    var treeDiv = document.getElementById("hierarchy-tree");

    fetch("/api/occupations/hierarchy")
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
                    var li = toggle.closest("li");
                    li.classList.toggle("collapsed");
                    toggle.setAttribute("aria-expanded",
                        li.classList.contains("collapsed") ? "false" : "true");
                }
            });
        })
        .catch(function() {
            treeDiv.innerHTML = '<p>Failed to load hierarchy.</p>';
        });

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
