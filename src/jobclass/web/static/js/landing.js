/* JobClass — Landing page: stats + showcase */
"use strict";

(function () {

    /* ================================================================
       1. Stats — rendered into hero
       ================================================================ */
    fetchWithTimeout("/api/stats")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var grid = document.getElementById("stats-grid");
            if (!grid) return;
            grid.innerHTML =
                statBadge(formatNumber(data.occupation_count), "Occupations") +
                statBadge(formatNumber(data.geography_count), "Geographies") +
                statBadge(formatNumber(data.skill_count), "Skills Tracked") +
                statBadge(formatNumber(data.task_count), "Tasks Tracked");
        })
        .catch(function () {});

    function statBadge(value, label) {
        return '<div class="landing-stat"><b>' + escapeHtml(value) + '</b>' + escapeHtml(label) + '</div>';
    }

    /* ================================================================
       2. Showcase — gradually transitioning content panels
       ================================================================ */
    var SLIDES = [
        {
            label: "Methodology",
            title: "What Lives in the Warehouse",
            link: "/methodology",
            linkText: "Methodology",
            bodyHtml:
                '<p>The warehouse organizes federal labor data into a star schema. Fact tables hold numeric ' +
                'measures &mdash; employment counts, wage percentiles, projected growth. Dimension tables hold ' +
                'descriptive context &mdash; occupation titles, geography names, skill definitions. Bridge tables ' +
                'connect the many-to-many relationships between occupations and their skills, knowledge areas, ' +
                'and abilities.</p>' +
                '<table><thead><tr><th>Table</th><th>Type</th><th>What It Holds</th></tr></thead><tbody>' +
                '<tr><td><code>dim_occupation</code></td><td>Dimension</td><td>870 SOC-coded occupations with four-level hierarchy</td></tr>' +
                '<tr><td><code>dim_geography</code></td><td>Dimension</td><td>National + 50 states + territories</td></tr>' +
                '<tr><td><code>fact_occupation_employment_wages</code></td><td>Fact</td><td>Employment counts and wage percentiles (10th&ndash;90th) by geography and vintage</td></tr>' +
                '<tr><td><code>bridge_occupation_skill</code></td><td>Bridge</td><td>35 skills per occupation with importance scores on a 1&ndash;5 scale</td></tr>' +
                '<tr><td><code>fact_occupation_projections</code></td><td>Fact</td><td>10-year employment outlook, growth rates, and annual openings</td></tr>' +
                '<tr><td><code>fact_time_series_observation</code></td><td>Fact</td><td>Multi-vintage time series: employment, wages, and derived metrics across years</td></tr>' +
                '</tbody></table>'
        },
        {
            label: "Lessons Learned",
            title: "Four Federal Sources, One Key",
            link: "/lessons#federal-data",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>Every table in the warehouse traces back to one of four federal programs, all published ' +
                'independently but joined by the Standard Occupational Classification (SOC) code. The SOC ' +
                'taxonomy is the backbone &mdash; it assigns a hierarchical code to each of roughly 870 ' +
                'occupations, and every other source references those codes.</p>' +
                '<table><thead><tr><th>Source</th><th>Agency</th><th>What It Provides</th><th>Frequency</th></tr></thead><tbody>' +
                '<tr><td><strong>SOC</strong></td><td>BLS</td><td>Occupation taxonomy: 23 major groups &rarr; 870 detailed codes</td><td>~10 years</td></tr>' +
                '<tr><td><strong>OEWS</strong></td><td>BLS</td><td>Employment counts and wage distributions by occupation and state</td><td>Annual</td></tr>' +
                '<tr><td><strong>O*NET</strong></td><td>DOL</td><td>Skills, knowledge, abilities, tasks, and education requirements</td><td>Semi-annual</td></tr>' +
                '<tr><td><strong>Projections</strong></td><td>BLS</td><td>10-year employment outlook with annual job openings</td><td>Biennial</td></tr>' +
                '</tbody></table>' +
                '<p>The pipeline downloads each source, parses its native format (XLSX, CSV, ZIP archives), ' +
                'validates against the previous release for schema drift, and loads into the warehouse. BLS ' +
                'endpoints require browser-like HTTP headers &mdash; the downloader sends <code>Sec-Fetch-*</code> ' +
                'headers to avoid being blocked.</p>'
        },
        {
            label: "Browse Hierarchy",
            title: "The SOC Code System",
            link: "/hierarchy",
            linkText: "Browse Hierarchy",
            bodyHtml:
                '<p>The Standard Occupational Classification assigns a hierarchical code to every occupation ' +
                'in the economy. The code encodes position in a four-level tree: major group, minor group, ' +
                'broad occupation, and detailed occupation. For example, SOC <code>11-1011</code> identifies ' +
                'Chief Executives &mdash; the <code>11</code> is Management, <code>1011</code> narrows to the specific role.</p>' +
                '<pre>SOC 2018 Hierarchy\n\n' +
                '11-0000  Management (Major Group)\n' +
                ' \u2514\u2500 11-1000  Top Executives (Minor Group)\n' +
                '     \u2514\u2500 11-1010  Chief Executives (Broad)\n' +
                '         \u2514\u2500 11-1011  Chief Executives (Detailed)\n\n' +
                '15-0000  Computer and Mathematical (Major Group)\n' +
                ' \u2514\u2500 15-1200  Software and Web Developers (Minor)\n' +
                '     \u2514\u2500 15-1250  Software and QA (Broad)\n' +
                '         \u2514\u2500 15-1252  Software Developers (Detailed)</pre>' +
                '<p>The taxonomy updates roughly every decade. When codes change, a crosswalk maps old codes to ' +
                'new ones, classifying each mapping as 1:1, split, merge, or complex. Only 1:1 mappings are safe ' +
                'for direct wage comparison; splits and merges require aggregation logic.</p>'
        },
        {
            label: "Lessons Learned",
            title: "Skill Profiles &mdash; 35 Dimensions per Occupation",
            link: "/lessons#similarity-algorithms",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>O*NET rates every occupation on 35 skills using an importance scale from 1 to 5. This is not ' +
                'binary (has / doesn&rsquo;t have) &mdash; every occupation has every skill, rated at different levels. ' +
                'The signal is in the <em>scores</em>, not the <em>membership</em>.</p>' +
                '<table><thead><tr><th>Skill</th><th>Software Developer</th><th>Registered Nurse</th><th>Accountant</th></tr></thead><tbody>' +
                '<tr><td>Active Listening</td><td>3.75</td><td>4.25</td><td>3.88</td></tr>' +
                '<tr><td>Critical Thinking</td><td>4.38</td><td>4.12</td><td>4.25</td></tr>' +
                '<tr><td>Programming</td><td>4.50</td><td>1.25</td><td>1.62</td></tr>' +
                '<tr><td>Mathematics</td><td>3.50</td><td>2.62</td><td>3.75</td></tr>' +
                '<tr><td>Writing</td><td>3.25</td><td>3.12</td><td>3.50</td></tr>' +
                '<tr><td>Monitoring</td><td>3.50</td><td>4.00</td><td>3.62</td></tr>' +
                '</tbody></table>' +
                '<p>Occupation similarity uses cosine similarity on these importance vectors. Jaccard similarity ' +
                '(set overlap) produces 100% matches for every pair because every occupation has every skill. ' +
                'Cosine compares the <em>direction</em> of the vectors, so occupations that emphasize the same skills ' +
                'at similar levels appear similar.</p>'
        },
        {
            label: "Pipeline Explorer",
            title: "Four-Layer Warehouse",
            link: "/lessons#idempotent-pipelines",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>Data flows through four layers, each with a clear responsibility and strict boundaries. ' +
                'No layer reaches into the layer below it or makes assumptions about the format of the layer above.</p>' +
                '<table><thead><tr><th>Layer</th><th>Purpose</th><th>Example</th></tr></thead><tbody>' +
                '<tr><td><strong>Raw</strong></td><td>Immutable byte-for-byte capture of downloaded files</td><td><code>raw/bls/oews_national/2023/</code></td></tr>' +
                '<tr><td><strong>Staging</strong></td><td>Parsed, typed, standardized columns &mdash; no denormalization</td><td><code>stage__bls__oews_national</code></td></tr>' +
                '<tr><td><strong>Core</strong></td><td>Conformed dimensions, facts, and bridges with version tracking</td><td><code>dim_occupation</code>, <code>fact_*</code></td></tr>' +
                '<tr><td><strong>Marts</strong></td><td>Denormalized, query-ready views for specific questions</td><td><code>mart_occupation_summary</code></td></tr>' +
                '</tbody></table>' +
                '<p>Every load operation is idempotent: re-running the same dataset version produces the same ' +
                'result without duplicates. The pattern is delete-before-insert at the version grain &mdash; ' +
                'delete all rows matching the incoming <code>source_release_id</code>, then insert the fresh parse. ' +
                'Grain uniqueness constraints catch any violations.</p>'
        },
        {
            label: "Trends & Movers",
            title: "Multi-Vintage Time Series",
            link: "/lessons#multi-vintage",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>OEWS publishes wage data annually. Each release is a vintage. Loading multiple vintages ' +
                'into the same table creates a time series, but naively unioning them produces duplicate rows &mdash; ' +
                'the same occupation appears once per vintage, often with different employment counts.</p>' +
                '<pre>-- Vintage-aware query: one row per year\n' +
                'SELECT year, soc_code,\n' +
                '       employment_count,\n' +
                '       median_annual_wage\n' +
                'FROM fact_time_series_observation\n' +
                'WHERE soc_code = \'15-1252\'\n' +
                '  AND metric_code = \'employment_count\'\n' +
                'ORDER BY year;\n\n' +
                '-- Result:\n' +
                '-- 2021  15-1252  1,622,300  $120,730\n' +
                '-- 2022  15-1252  1,670,500  $127,260\n' +
                '-- 2023  15-1252  1,795,300  $132,270</pre>' +
                '<p>The time-series layer normalizes these snapshots into observation facts with explicit ' +
                'vintage tracking. Derived metrics &mdash; year-over-year change, rolling averages &mdash; are computed ' +
                'in a separate fact table so raw observations stay untouched.</p>'
        },
        {
            label: "Search Occupations",
            title: "Wage Distribution &mdash; What an Occupation Earns",
            link: "/search",
            linkText: "Search Occupations",
            bodyHtml:
                '<p>OEWS reports wage distributions at seven percentile points plus mean and median, ' +
                'for both hourly and annual rates. Each row is specific to an occupation, geography (national ' +
                'or state), and survey year.</p>' +
                '<table><thead><tr><th>Field</th><th>Software Developers</th><th>Registered Nurses</th></tr></thead><tbody>' +
                '<tr><td>Employment</td><td>1,795,300</td><td>3,175,390</td></tr>' +
                '<tr><td>Mean Annual Wage</td><td>$132,930</td><td>$89,010</td></tr>' +
                '<tr><td>Median Annual Wage</td><td>$132,270</td><td>$86,070</td></tr>' +
                '<tr><td>10th Percentile</td><td>$74,400</td><td>$60,270</td></tr>' +
                '<tr><td>90th Percentile</td><td>$208,620</td><td>$129,400</td></tr>' +
                '</tbody></table>' +
                '<p>Wages are stored as-published (nominal dollars). The warehouse also computes ' +
                'inflation-adjusted real wages using CPI-U with 2023 as the base year: ' +
                '<code>real_wage = nominal &times; (CPI_2023 / CPI_year)</code>. This makes cross-year ' +
                'wage comparisons meaningful.</p>'
        },
        {
            label: "Pipeline Explorer",
            title: "From Dynamic API to Static Site",
            link: "/lessons#fetch-shim",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>This site runs on GitHub Pages &mdash; no server. A build script pre-renders every HTML page ' +
                'and every API response as static files. A JavaScript fetch shim injected into each page intercepts ' +
                '<code>fetch()</code> calls to <code>/api/</code> and redirects them to the corresponding ' +
                '<code>.json</code> files on disk.</p>' +
                '<pre>// The shim intercepts fetch() calls:\nvar originalFetch = window.fetch;\n' +
                'window.fetch = function(url) {\n' +
                '  if (url.indexOf(\'/api/\') &lt; 0)\n' +
                '    return originalFetch(url);\n\n' +
                '  // /api/occupations/15-1252/wages?geo_type=state\n' +
                '  // becomes /api/occupations/15-1252/wages-state.json\n' +
                '  return originalFetch(mapToStatic(url));\n' +
                '};</pre>' +
                '<p>Search works by downloading the full 870-occupation index once and filtering client-side. ' +
                'The comparison endpoint, which accepts arbitrary SOC code combinations, fetches individual ' +
                'occupation JSON files and assembles the response in the browser. The same codebase serves ' +
                'both the live FastAPI server and the static GitHub Pages deployment.</p>'
        },
        {
            label: "Methodology",
            title: "Schema Drift &amp; Validation Gates",
            link: "/lessons#schema-drift",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>Federal data sources change format between releases &mdash; columns are added, renamed, or ' +
                'retyped without warning. The pipeline detects these changes before they reach the warehouse.</p>' +
                '<p>Three validation gates run before any data is published:</p>' +
                '<table><thead><tr><th>Gate</th><th>What It Catches</th><th>Example</th></tr></thead><tbody>' +
                '<tr><td><strong>Schema comparison</strong></td><td>Column adds, removes, type changes</td><td>OEWS renamed <code>OCC_CODE</code> to <code>O_CODE</code></td></tr>' +
                '<tr><td><strong>Row count shift</strong></td><td>Unexpected volume changes</td><td>State file dropped from 50 to 48 rows</td></tr>' +
                '<tr><td><strong>Measure delta</strong></td><td>Key values change beyond threshold</td><td>National mean wage jumped 40% between releases</td></tr>' +
                '</tbody></table>' +
                '<p>If any gate fails, the entire publication is blocked &mdash; no partial loads. Because raw ' +
                'files are stored immutably, a parser fix can be tested against the exact data that exposed the ' +
                'problem without waiting for a fresh download.</p>'
        },
        {
            label: "Lessons Learned",
            title: "Dimensional Modeling &mdash; Star Schema Design",
            link: "/lessons#dimensional-modeling",
            linkText: "Lessons Learned",
            bodyHtml:
                '<p>The warehouse uses a star schema: fact tables hold numeric measures (how many, how much) ' +
                'and dimension tables hold descriptive context (what, where, when). This separation means a single ' +
                'occupation dimension serves wages, skills, projections, and time-series facts simultaneously.</p>' +
                '<pre>-- One dimension, many facts:\n\n' +
                'dim_occupation\n' +
                '  \u251c\u2500 fact_occupation_employment_wages\n' +
                '  \u251c\u2500 fact_occupation_projections\n' +
                '  \u251c\u2500 fact_time_series_observation\n' +
                '  \u251c\u2500 bridge_occupation_skill\n' +
                '  \u251c\u2500 bridge_occupation_knowledge\n' +
                '  \u2514\u2500 bridge_occupation_ability\n\n' +
                'dim_geography\n' +
                '  \u2514\u2500 fact_occupation_employment_wages</pre>' +
                '<p>Surrogate keys (auto-incrementing integers) decouple warehouse identity from source codes. ' +
                'This lets the same SOC code appear in multiple vintages without key collision, and enables ' +
                'the time-series layer to track how an occupation&rsquo;s data evolves across releases.</p>'
        }
    ];

    /* ================================================================
       2b. Showcase — rendering + controls
       ================================================================ */
    var viewport = document.getElementById("showcase-viewport");
    var dotsContainer = document.getElementById("showcase-dots");
    var prevBtn = document.getElementById("showcase-prev");
    var nextBtn = document.getElementById("showcase-next");
    var pauseBtn = document.getElementById("showcase-pause");
    var current = 0;
    var timer = null;
    var paused = false;
    var INTERVAL = 18000; /* 18 seconds — gradual pace */

    if (viewport) {
        buildShowcase();
        startTimer();
    }

    function buildShowcase() {
        var html = "";
        for (var i = 0; i < SLIDES.length; i++) {
            var s = SLIDES[i];
            html += '<div class="showcase-slide' + (i === 0 ? ' active' : '') + '">';
            html += '<div class="showcase-slide-label">' + escapeHtml(s.label) + '</div>';
            html += '<div class="showcase-slide-title">';
            html += '<h3>' + s.title + '</h3>';
            if (s.link) {
                html += '<a href="' + escapeAttr(s.link) + '" class="showcase-link">' + escapeHtml(s.linkText || "Learn more") + ' &#8594;</a>';
            }
            html += '</div>';
            html += '<div class="showcase-body">' + s.bodyHtml + '</div>';
            html += '</div>';
        }
        viewport.innerHTML = html;

        /* Dots */
        if (dotsContainer) {
            var dots = "";
            for (var d = 0; d < SLIDES.length; d++) {
                dots += '<button class="dot' + (d === 0 ? ' active' : '') + '" data-idx="' + d + '" aria-label="Slide ' + (d + 1) + ' &mdash; ' + escapeAttr(SLIDES[d].title) + '"></button>';
            }
            dotsContainer.innerHTML = dots;
            dotsContainer.addEventListener("click", function (e) {
                var btn = e.target.closest(".dot");
                if (!btn) return;
                goTo(parseInt(btn.getAttribute("data-idx"), 10));
                resetTimer();
            });
        }

        if (prevBtn) prevBtn.addEventListener("click", function () { goTo(current - 1); resetTimer(); });
        if (nextBtn) nextBtn.addEventListener("click", function () { goTo(current + 1); resetTimer(); });
        if (pauseBtn) pauseBtn.addEventListener("click", togglePause);
    }

    function goTo(idx) {
        idx = ((idx % SLIDES.length) + SLIDES.length) % SLIDES.length;
        if (idx === current) return;
        var slides = viewport.querySelectorAll(".showcase-slide");
        slides[current].classList.remove("active");
        slides[idx].classList.add("active");
        current = idx;
        updateDots();
    }

    function updateDots() {
        if (!dotsContainer) return;
        var dots = dotsContainer.querySelectorAll(".dot");
        for (var i = 0; i < dots.length; i++) {
            dots[i].classList.toggle("active", i === current);
        }
    }

    function startTimer() {
        timer = setInterval(function () { goTo(current + 1); }, INTERVAL);
    }

    function resetTimer() {
        clearInterval(timer);
        if (!paused) startTimer();
    }

    function togglePause() {
        paused = !paused;
        if (paused) {
            clearInterval(timer);
            pauseBtn.innerHTML = '&#9654;';
            pauseBtn.setAttribute('aria-label', 'Play');
        } else {
            startTimer();
            pauseBtn.innerHTML = '&#10074;&#10074;';
            pauseBtn.setAttribute('aria-label', 'Pause');
        }
    }

})();
