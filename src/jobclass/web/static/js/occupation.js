/* JobClass — Occupation profile page */
"use strict";

(function() {
    var socCode = document.getElementById("occupation-page").dataset.socCode;
    var loading = document.getElementById("profile-loading");
    var content = document.getElementById("profile-content");

    function showError(elementId, message) {
        var el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = '<p class="error-message">' + escapeHtml(message) + '</p>';
        }
    }

    function showNoData(sectionId, contentId, message) {
        var section = document.getElementById(sectionId);
        if (section) section.style.display = "block";
        var el = document.getElementById(contentId);
        if (el) el.innerHTML = '<p class="no-data-message">' + escapeHtml(message) + '</p>';
    }

    function setBusy(sectionId, busy) {
        var el = document.getElementById(sectionId);
        if (el) el.setAttribute("aria-busy", busy ? "true" : "false");
    }

    fetchWithTimeout("/api/occupations/" + encodeURIComponent(socCode))
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
            // Load knowledge
            loadKnowledge(socCode);
            // Load abilities
            loadAbilities(socCode);
            // Load tasks
            loadTasks(socCode);
            // Load projections
            loadProjections(socCode);
            // Load similar
            loadSimilar(socCode);
        })
        .catch(function() {
            loading.innerHTML = '<p class="error-message">Occupation not found or request timed out.</p><p><a href="/search">Return to Search</a></p>';
        });

    function loadWages(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/wages?geo_type=national")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("wages-section", false);
                if (!data || !data.wages || data.wages.length === 0) {
                    showNoData("wages-section", "wages-content", "No wage data available for this occupation. OEWS does not cover all SOC codes (e.g., military occupations).");
                    return;
                }
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
                html += '<p id="compare-state-link" style="display:none;"><a href="/occupation/' + escapeAttr(code) + '/wages" class="btn">Compare by State</a></p>';
                html += '<div class="lineage-badge">OEWS ' + escapeHtml(w.source_release_id) + ' | ' + escapeHtml(w.reference_period) + '</div>';
                document.getElementById("wages-content").innerHTML = html;

                // Only show "Compare by State" if state-level data exists
                fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/wages?geo_type=state")
                    .then(function(r) { return r.ok ? r.json() : null; })
                    .then(function(stateData) {
                        if (stateData && stateData.wages && stateData.wages.length > 0) {
                            var link = document.getElementById("compare-state-link");
                            if (link) link.style.display = "";
                        }
                    })
                    .catch(function() {});
            })
            .catch(function() {
                setBusy("wages-section", false);
                document.getElementById("wages-section").style.display = "block";
                showError("wages-content", "Failed to load wage data.");
            });
    }

    function loadSkills(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/skills")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("skills-section", false);
                if (!data || !data.skills || data.skills.length === 0) {
                    showNoData("skills-section", "skills-content", "No skills data available. O*NET does not cover all SOC codes.");
                    return;
                }
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
            })
            .catch(function() {
                setBusy("skills-section", false);
                document.getElementById("skills-section").style.display = "block";
                showError("skills-content", "Failed to load skills data.");
            });
    }

    function loadKnowledge(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/knowledge")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("knowledge-section", false);
                if (!data || !data.knowledge || data.knowledge.length === 0) {
                    showNoData("knowledge-section", "knowledge-content", "No knowledge data available.");
                    return;
                }
                var section = document.getElementById("knowledge-section");
                section.style.display = "block";
                var html = '<table class="data-table"><thead><tr><th>Knowledge Domain</th><th>Importance</th><th>Level</th></tr></thead><tbody>';
                data.knowledge.forEach(function(k) {
                    html += '<tr><td>' + escapeHtml(k.element_name) + '</td>';
                    html += '<td>' + (k.importance != null ? k.importance.toFixed(2) : 'N/A') + '</td>';
                    html += '<td>' + (k.level != null ? k.level.toFixed(2) : 'N/A') + '</td></tr>';
                });
                html += '</tbody></table>';
                if (data.source_version) html += '<div class="lineage-badge">O*NET ' + escapeHtml(data.source_version) + '</div>';
                document.getElementById("knowledge-content").innerHTML = html;
            })
            .catch(function() {
                setBusy("knowledge-section", false);
                document.getElementById("knowledge-section").style.display = "block";
                showError("knowledge-content", "Failed to load knowledge data.");
            });
    }

    function loadAbilities(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/abilities")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("abilities-section", false);
                if (!data || !data.abilities || data.abilities.length === 0) {
                    showNoData("abilities-section", "abilities-content", "No abilities data available.");
                    return;
                }
                var section = document.getElementById("abilities-section");
                section.style.display = "block";
                var html = '<table class="data-table"><thead><tr><th>Ability</th><th>Importance</th><th>Level</th></tr></thead><tbody>';
                data.abilities.forEach(function(a) {
                    html += '<tr><td>' + escapeHtml(a.element_name) + '</td>';
                    html += '<td>' + (a.importance != null ? a.importance.toFixed(2) : 'N/A') + '</td>';
                    html += '<td>' + (a.level != null ? a.level.toFixed(2) : 'N/A') + '</td></tr>';
                });
                html += '</tbody></table>';
                if (data.source_version) html += '<div class="lineage-badge">O*NET ' + escapeHtml(data.source_version) + '</div>';
                document.getElementById("abilities-content").innerHTML = html;
            })
            .catch(function() {
                setBusy("abilities-section", false);
                document.getElementById("abilities-section").style.display = "block";
                showError("abilities-content", "Failed to load abilities data.");
            });
    }

    function loadTasks(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/tasks")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("tasks-section", false);
                if (!data || !data.tasks || data.tasks.length === 0) {
                    showNoData("tasks-section", "tasks-content", "No task data available. O*NET does not cover all SOC codes.");
                    return;
                }
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
            })
            .catch(function() {
                setBusy("tasks-section", false);
                document.getElementById("tasks-section").style.display = "block";
                showError("tasks-content", "Failed to load tasks data.");
            });
    }

    function loadProjections(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/projections")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("projections-section", false);
                if (!data || !data.projections) {
                    showNoData("projections-section", "projections-content", "No projection data available. BLS projections do not cover all SOC codes.");
                    return;
                }
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
            })
            .catch(function() {
                setBusy("projections-section", false);
                document.getElementById("projections-section").style.display = "block";
                showError("projections-content", "Failed to load projections data.");
            });
    }

    function loadSimilar(code) {
        fetchWithTimeout("/api/occupations/" + encodeURIComponent(code) + "/similar")
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                setBusy("similar-section", false);
                if (!data || !data.similar || data.similar.length === 0) {
                    showNoData("similar-section", "similar-content", "No similarity data available for this occupation.");
                    return;
                }
                var section = document.getElementById("similar-section");
                section.style.display = "block";
                var html = '<table class="data-table"><thead><tr><th>Occupation</th><th>Similarity</th></tr></thead><tbody>';
                data.similar.forEach(function(s) {
                    html += '<tr><td><a href="/occupation/' + escapeAttr(s.soc_code) + '">' + escapeHtml(s.soc_code) + ' — ' + escapeHtml(s.occupation_title) + '</a></td>';
                    html += '<td>' + (s.similarity_score * 100).toFixed(1) + '%</td></tr>';
                });
                html += '</tbody></table>';
                document.getElementById("similar-content").innerHTML = html;
            })
            .catch(function() {
                setBusy("similar-section", false);
                document.getElementById("similar-section").style.display = "block";
                showError("similar-content", "Failed to load similar occupations.");
            });
    }

    function wageCard(label, value) {
        return '<div class="stat-card"><div class="stat-label">' + label + '</div><div class="stat-value">' + value + '</div></div>';
    }

})();
