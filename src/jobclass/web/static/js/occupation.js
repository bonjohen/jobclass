/* JobClass — Occupation profile page */
"use strict";

(function() {
    var socCode = document.getElementById("occupation-page").dataset.socCode;
    var loading = document.getElementById("profile-loading");
    var content = document.getElementById("profile-content");

    fetch("/api/occupations/" + encodeURIComponent(socCode))
        .then(function(r) {
            if (!r.ok) throw new Error("Not found");
            return r.json();
        })
        .then(function(data) {
            loading.style.display = "none";
            content.style.display = "block";

            // Title and meta
            document.getElementById("occ-title").textContent = data.occupation_title;
            document.getElementById("occ-soc-code").textContent = data.soc_code;
            document.getElementById("occ-soc-version").textContent = "SOC " + data.soc_version;
            document.title = data.occupation_title + " (" + data.soc_code + ") — JobClass";

            // Definition
            if (data.occupation_definition) {
                document.getElementById("occ-definition").textContent = data.occupation_definition;
            } else {
                document.getElementById("definition-section").style.display = "none";
            }

            // Breadcrumb
            if (data.breadcrumb && data.breadcrumb.length > 0) {
                var bc = document.getElementById("breadcrumb");
                var html = "";
                data.breadcrumb.forEach(function(item, i) {
                    if (i > 0) html += ' <span class="bc-sep">&rsaquo;</span> ';
                    if (item.soc_code === socCode) {
                        html += '<span class="bc-current">' + escapeHtml(item.occupation_title) + '</span>';
                    } else {
                        html += '<a href="/occupation/' + escapeAttr(item.soc_code) + '">' + escapeHtml(item.occupation_title) + '</a>';
                    }
                });
                bc.innerHTML = html;
            }

            // Siblings
            if (data.siblings && data.siblings.length > 0) {
                document.getElementById("siblings-section").style.display = "block";
                var sl = document.getElementById("siblings-list");
                sl.innerHTML = data.siblings.map(function(s) {
                    return '<li><a href="/occupation/' + escapeAttr(s.soc_code) + '">' + escapeHtml(s.soc_code) + ' — ' + escapeHtml(s.occupation_title) + '</a></li>';
                }).join("");
            }

            // Children
            if (data.children && data.children.length > 0) {
                document.getElementById("children-section").style.display = "block";
                var cl = document.getElementById("children-list");
                cl.innerHTML = data.children.map(function(c) {
                    return '<li><a href="/occupation/' + escapeAttr(c.soc_code) + '">' + escapeHtml(c.soc_code) + ' — ' + escapeHtml(c.occupation_title) + '</a></li>';
                }).join("");
            }

            // Load wages
            loadWages(socCode);
            // Load skills
            loadSkills(socCode);
            // Load tasks
            loadTasks(socCode);
            // Load projections
            loadProjections(socCode);
            // Load similar
            loadSimilar(socCode);
        })
        .catch(function() {
            loading.innerHTML = '<p>Occupation not found.</p><p><a href="/search">Return to Search</a></p>';
        });

    function loadWages(code) {
        fetch("/api/occupations/" + encodeURIComponent(code) + "/wages?geo_type=national")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.wages || data.wages.length === 0) return;
                var w = data.wages[0];
                var section = document.getElementById("wages-section");
                section.style.display = "block";
                var html = '<div class="wages-grid">';
                html += wageCard("Employment", formatNumber(w.employment_count));
                html += wageCard("Mean Annual Wage", formatWage(w.mean_annual_wage));
                html += wageCard("Median Annual Wage", formatWage(w.median_annual_wage));
                html += '</div>';
                html += '<h3>Wage Distribution (Hourly)</h3>';
                html += '<div class="wage-distribution">';
                html += '<table class="data-table"><thead><tr>';
                html += '<th>P10</th><th>P25</th><th>Median</th><th>P75</th><th>P90</th>';
                html += '</tr></thead><tbody><tr>';
                html += '<td>' + formatWage(w.p10_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p25_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.median_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p75_hourly_wage) + '</td>';
                html += '<td>' + formatWage(w.p90_hourly_wage) + '</td>';
                html += '</tr></tbody></table></div>';
                html += '<p><a href="/occupation/' + escapeAttr(code) + '/wages" class="btn">Compare by State</a></p>';
                html += '<div class="lineage-badge">OEWS ' + escapeHtml(w.source_release_id) + ' | ' + escapeHtml(w.reference_period) + '</div>';
                document.getElementById("wages-content").innerHTML = html;
            });
    }

    function loadSkills(code) {
        fetch("/api/occupations/" + encodeURIComponent(code) + "/skills")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.skills || data.skills.length === 0) return;
                var section = document.getElementById("skills-section");
                section.style.display = "block";
                var html = '<table class="data-table"><thead><tr><th>Skill</th><th>Importance</th><th>Level</th></tr></thead><tbody>';
                data.skills.forEach(function(s) {
                    html += '<tr><td>' + escapeHtml(s.element_name) + '</td>';
                    html += '<td>' + (s.importance != null ? s.importance.toFixed(2) : 'N/A') + '</td>';
                    html += '<td>' + (s.level != null ? s.level.toFixed(2) : 'N/A') + '</td></tr>';
                });
                html += '</tbody></table>';
                if (data.source_version) html += '<div class="lineage-badge">O*NET ' + escapeHtml(data.source_version) + '</div>';
                document.getElementById("skills-content").innerHTML = html;
            });
    }

    function loadTasks(code) {
        fetch("/api/occupations/" + encodeURIComponent(code) + "/tasks")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.tasks || data.tasks.length === 0) return;
                var section = document.getElementById("tasks-section");
                section.style.display = "block";
                var html = '<ul class="task-list">';
                data.tasks.forEach(function(t) {
                    html += '<li>' + escapeHtml(t.task_description);
                    if (t.relevance_score != null) html += ' <span class="relevance-score">(' + t.relevance_score.toFixed(2) + ')</span>';
                    html += '</li>';
                });
                html += '</ul>';
                if (data.source_version) html += '<div class="lineage-badge">O*NET ' + escapeHtml(data.source_version) + '</div>';
                document.getElementById("tasks-content").innerHTML = html;
            });
    }

    function loadProjections(code) {
        fetch("/api/occupations/" + encodeURIComponent(code) + "/projections")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.projections) return;
                var p = data.projections;
                var section = document.getElementById("projections-section");
                section.style.display = "block";
                var html = '<div class="wages-grid">';
                html += wageCard("Base Employment (" + escapeHtml(p.base_year) + ")", formatNumber(p.base_employment));
                html += wageCard("Projected Employment (" + escapeHtml(p.projection_year) + ")", formatNumber(p.projected_employment));
                html += wageCard("Growth Rate", p.percent_change != null ? p.percent_change.toFixed(1) + "%" : "N/A");
                html += wageCard("Annual Openings", formatNumber(p.annual_openings));
                html += '</div>';
                if (p.education_category) {
                    html += '<p><strong>Typical Education:</strong> ' + escapeHtml(p.education_category) + '</p>';
                }
                if (p.source_release_id) html += '<div class="lineage-badge">Projections ' + escapeHtml(p.projection_cycle) + ' | ' + escapeHtml(p.source_release_id) + '</div>';
                document.getElementById("projections-content").innerHTML = html;
            });
    }

    function loadSimilar(code) {
        fetch("/api/occupations/" + encodeURIComponent(code) + "/similar")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.similar || data.similar.length === 0) return;
                var section = document.getElementById("similar-section");
                section.style.display = "block";
                var html = '<table class="data-table"><thead><tr><th>Occupation</th><th>Similarity</th></tr></thead><tbody>';
                data.similar.forEach(function(s) {
                    html += '<tr><td><a href="/occupation/' + escapeAttr(s.soc_code) + '">' + escapeHtml(s.soc_code) + ' — ' + escapeHtml(s.occupation_title) + '</a></td>';
                    html += '<td>' + (s.similarity_score * 100).toFixed(1) + '%</td></tr>';
                });
                html += '</tbody></table>';
                document.getElementById("similar-content").innerHTML = html;
            });
    }

    function wageCard(label, value) {
        return '<div class="stat-card"><div class="stat-label">' + label + '</div><div class="stat-value">' + value + '</div></div>';
    }

})();
