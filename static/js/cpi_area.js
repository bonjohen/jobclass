"use strict";
(function() {
    var page = document.getElementById("cpi-area-page");
    if (!page) return;
    var areaCode = page.getAttribute("data-area-code");
    if (!areaCode) return;

    var loadingEl = document.getElementById("area-loading");
    var contentEl = document.getElementById("area-content");

    // Fetch area detail
    fetchWithTimeout("/api/cpi/areas/" + encodeURIComponent(areaCode))
        .then(function(r) {
            if (!r.ok) throw new Error("not found");
            return r.json();
        })
        .then(function(area) {
            loadingEl.style.display = "none";
            contentEl.style.display = "block";

            document.getElementById("area-title").textContent = area.area_title;
            document.getElementById("area-breadcrumb-name").textContent = area.area_title;
            document.getElementById("area-code-badge").textContent = area.area_code;
            document.getElementById("area-type-badge").textContent = area.area_type;
            document.getElementById("area-freq-badge").textContent = area.publication_frequency;
            document.getElementById("area-member-count").textContent = area.member_count;

            // Show caveats
            var caveats = [];
            caveats.push("Area indexes do not measure price-level differences among cities. " +
                "A higher index for one area does not mean prices are higher there than in another area with a lower index.");
            if (area.publication_frequency === "bimonthly") {
                caveats.push("This area is published bimonthly (every other month). " +
                    "Time-series data will have natural gaps between publication months.");
            }
            if (area.area_type === "metro") {
                caveats.push("Metropolitan area indexes are subject to greater sampling variability " +
                    "than regional or national indexes.");
            }
            var caveatHtml = caveats.map(function(c) {
                return '<div class="cpi-caveat">' + escapeHtml(c) + '</div>';
            }).join("");
            document.getElementById("area-caveats").innerHTML = caveatHtml;

            // Load members
            loadAreaMembers(areaCode);
        })
        .catch(function() {
            loadingEl.textContent = "CPI area not found.";
        });

    var allMembers = [];

    function loadAreaMembers(ac) {
        fetchWithTimeout("/api/cpi/areas/" + encodeURIComponent(ac) + "/members")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                allMembers = data.members || [];
                renderMembers(allMembers);
            })
            .catch(function() {});
    }

    function renderMembers(members) {
        var list = document.getElementById("area-members-list");
        if (members.length === 0) {
            list.innerHTML = '<li class="cpi-member-item">No members found.</li>';
            return;
        }
        var html = "";
        members.forEach(function(m) {
            html += '<li class="cpi-member-item">';
            html += '<a href="/cpi/member/' + escapeAttr(m.member_code) + '">';
            html += '<span class="cpi-code">' + escapeHtml(m.member_code) + '</span> ';
            html += escapeHtml(m.title);
            html += '</a>';
            if (m.semantic_role && m.semantic_role !== "hierarchy_node") {
                html += ' <span class="cpi-role-badge">' + escapeHtml(m.semantic_role) + '</span>';
            }
            html += '</li>';
        });
        list.innerHTML = html;
    }

    // Filter
    document.getElementById("area-member-filter").addEventListener("input", function() {
        var q = this.value.toLowerCase();
        if (!q) {
            renderMembers(allMembers);
            return;
        }
        var filtered = allMembers.filter(function(m) {
            return m.member_code.toLowerCase().indexOf(q) >= 0 || m.title.toLowerCase().indexOf(q) >= 0;
        });
        renderMembers(filtered);
    });
})();
