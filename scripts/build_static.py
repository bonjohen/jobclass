#!/usr/bin/env python3
"""Static site generator for JobClass GitHub Pages deployment.

Generates a complete static site from the warehouse database by:
1. Rendering all HTML pages via the FastAPI TestClient
2. Pre-generating all API responses as JSON files
3. Injecting a fetch shim that redirects API calls to static JSON files
4. Rewriting paths for GitHub Pages subpath deployment

Usage:
    python scripts/build_static.py --base-path /jobclass

Prerequisites:
    - warehouse.duckdb must be populated (run `jobclass-pipeline run-all`)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import sys
import time
from pathlib import Path

# Ensure project is importable
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))


# ---------------------------------------------------------------------------
# Fetch shim — injected into <head> of every static HTML page.
# Intercepts fetch() calls to /api/ and redirects to pre-built .json files.
# Search uses a cached full index with client-side filtering.
# Wages endpoints map geo_type param to separate files.
# ---------------------------------------------------------------------------

STATIC_SHIM = r"""<script>
(function(){
var F=window.fetch,SC=null;
function LS(b){
  if(!SC)SC=F(b+'/api/occupations/search.json').then(function(r){return r.json()});
  return SC;
}
window.fetch=function(u){
  if(typeof u!=='string')return F.apply(this,arguments);
  var ai=u.indexOf('/api/');
  if(ai<0)return F.apply(this,arguments);
  var b=u.substring(0,ai),r=u.substring(ai);
  var qi=r.indexOf('?'),p=qi>=0?r.substring(0,qi):r;
  var sp=new URLSearchParams(qi>=0?r.substring(qi+1):'');
  if(p==='/api/occupations/search'){
    return LS(b).then(function(d){
      var q=(sp.get('q')||'').toLowerCase(),
          lm=+(sp.get('limit')||50),of=+(sp.get('offset')||0),
          rs=d.results||[];
      if(q)rs=rs.filter(function(x){
        return x.soc_code.toLowerCase().indexOf(q)>=0||
               x.occupation_title.toLowerCase().indexOf(q)>=0;
      });
      return new Response(JSON.stringify({
        results:rs.slice(of,of+lm),total:rs.length,limit:lm,offset:of
      }),{headers:{'Content-Type':'application/json'}});
    });
  }
  var pts=p.split('/');
  if(pts.length===5&&pts[4]==='wages'&&pts[2]==='occupations'){
    return F(b+'/api/occupations/'+pts[3]+'/wages-'+(sp.get('geo_type')||'national')+'.json');
  }
  if(p==='/api/trends/movers'){
    var yr=sp.get('year'),mt=sp.get('metric')||'employment_count';
    var mf=mt==='employment_count'?'':'_'+mt;
    if(yr)return F(b+'/api/trends/movers-'+yr+mf+'.json');
    return F(b+'/api/trends/movers'+mf+'.json');
  }
  if(p==='/api/trends/compare/occupations'){
    var codes=(sp.get('soc_codes')||'').split(',').filter(Boolean);
    var met=sp.get('metric')||'employment_count';
    var gt=sp.get('geo_type')||'national';
    return Promise.all(codes.map(function(c){
      var ct=c.trim();
      var tf=met==='employment_count'?ct+'.json':ct+'-'+met+'.json';
      return Promise.all([
        F(b+'/api/trends/'+tf).then(function(r){return r.json()})
          .catch(function(e){console.warn('shim:trend',ct,e);return null}),
        F(b+'/api/occupations/'+ct+'.json').then(function(r){return r.json()})
          .catch(function(e){console.warn('shim:occ',ct,e);return null})
      ]);
    })).then(function(arr){
      var occs=[];
      arr.forEach(function(pair,i){
        var d=pair[0],info=pair[1];
        if(!d||!d.series)return;
        var title=(info&&info.occupation_title)?info.occupation_title:codes[i];
        occs.push({soc_code:codes[i],title:title,series:d.series.map(function(s){return{year:s.year,value:s.value}})});
      });
      var body=JSON.stringify({metric:met,geo_type:gt,occupations:occs});
      return new Response(body,{headers:{'Content-Type':'application/json'}});
    });
  }
  if(pts.length===4&&pts[1]==='api'&&pts[2]==='trends'&&/^\d{2}-\d{4}$/.test(pts[3])){
    var tm=sp.get('metric');
    if(tm&&tm!=='employment_count')return F(b+'/api/trends/'+pts[3]+'-'+tm+'.json');
    return F(b+'/api/trends/'+pts[3]+'.json');
  }
  if(p==='/api/trends/compare/geography'){
    var sc=sp.get('soc_code');
    if(sc)return F(b+'/api/trends/compare/geography-'+sc+'.json');
  }
  if(p==='/api/cpi/search'){
    return F(b+'/api/cpi/search.json').then(function(r){return r.json()}).then(function(d){
      var q2=(sp.get('q')||'').toLowerCase(),lm2=+(sp.get('limit')||50),
          rs2=d.results||[];
      if(q2)rs2=rs2.filter(function(x){
        return x.member_code.toLowerCase().indexOf(q2)>=0||x.title.toLowerCase().indexOf(q2)>=0;
      });
      return new Response(JSON.stringify({query:sp.get('q')||'',total:rs2.length,results:rs2.slice(0,lm2)}),
        {headers:{'Content-Type':'application/json'}});
    });
  }
  return F(b+p+'.json');
};
})();
</script>"""


# ---------------------------------------------------------------------------
# Path rewriting for GitHub Pages subpath (e.g., /jobclass)
# ---------------------------------------------------------------------------


def rewrite_paths(content: str, base_path: str) -> str:
    """Rewrite absolute URL paths to include the GitHub Pages base path."""
    if not base_path:
        return content
    bp = base_path
    replacements = [
        # JS fetch / template literals
        ('"/api/', f'"{bp}/api/'),
        ("'/api/", f"'{bp}/api/"),
        ("`/api/", f"`{bp}/api/"),
        # Occupation page links (in JS-generated HTML and templates)
        ('"/occupation/', f'"{bp}/occupation/'),
        ("'/occupation/", f"'{bp}/occupation/"),
        ("`/occupation/", f"`{bp}/occupation/"),
        # Nav links
        ('"/search"', f'"{bp}/search"'),
        ("'/search'", f"'{bp}/search'"),
        ('"/hierarchy"', f'"{bp}/hierarchy"'),
        ("'/hierarchy'", f"'{bp}/hierarchy'"),
        ('"/methodology"', f'"{bp}/methodology"'),
        ("'/methodology'", f"'{bp}/methodology'"),
        # CPI links
        ('"/cpi"', f'"{bp}/cpi"'),
        ("'/cpi'", f"'{bp}/cpi'"),
        ('"/cpi/', f'"{bp}/cpi/'),
        ("'/cpi/", f"'{bp}/cpi/"),
        # Trend links
        ('"/trends"', f'"{bp}/trends"'),
        ("'/trends'", f"'{bp}/trends'"),
        ('"/trends/', f'"{bp}/trends/'),
        ("'/trends/", f"'{bp}/trends/"),
        ("`/trends/", f"`{bp}/trends/"),
        # Lesson links
        ('"/lessons"', f'"{bp}/lessons"'),
        ("'/lessons'", f"'{bp}/lessons'"),
        ('"/lessons/', f'"{bp}/lessons/'),
        ("'/lessons/", f"'{bp}/lessons/"),
        # Static assets
        ('"/static/', f'"{bp}/static/'),
        ("'/static/", f"'{bp}/static/"),
        # Root link
        ('href="/"', f'href="{bp}/"'),
        # Skip-to-content (hash link is fine, but href="/" in nav)
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    return content


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_static(base_path: str, output_dir: str) -> None:
    import duckdb
    from starlette.testclient import TestClient

    from jobclass.web.app import create_app
    from jobclass.web.database import get_db, reset_db, set_db

    output = Path(output_dir)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    bp = base_path.rstrip("/") if base_path != "/" else ""

    # --- Get occupation list ---
    # Use a single shared connection to avoid DuckDB file-lock deadlocks
    # on Windows when the TestClient thread pool opens multiple connections.
    db = get_db()
    db_path = db.execute("PRAGMA database_list").fetchone()[2]
    db.close()
    reset_db()
    shared_conn = duckdb.connect(db_path, read_only=True)
    set_db(shared_conn)
    db = shared_conn

    soc_codes = [
        r[0]
        for r in db.execute("SELECT soc_code FROM dim_occupation WHERE is_current = true ORDER BY soc_code").fetchall()
    ]
    print(f"Building static site for {len(soc_codes)} occupations")

    # --- Create test client ---
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)

    # --- Copy static assets ---
    static_src = _project_root / "src" / "jobclass" / "web" / "static"
    static_dst = output / "static"
    if static_src.exists():
        shutil.copytree(static_src, static_dst)
        # Rewrite paths in JS files for base path
        if bp:
            for js_file in static_dst.rglob("*.js"):
                content = js_file.read_text(encoding="utf-8")
                rewritten = rewrite_paths(content, bp)
                if rewritten != content:
                    js_file.write_text(rewritten, encoding="utf-8")
    print("  Copied static assets")

    # --- Helpers ---
    def write_html(url: str, filepath: str) -> bool:
        resp = client.get(url)
        if resp.status_code not in (200, 404):
            return False
        html = resp.text
        # FIRST: rewrite paths for base path (affects original content only)
        if bp:
            html = rewrite_paths(html, bp)
        # THEN: inject fetch shim (its /api/ paths must NOT be rewritten —
        # the shim's `b` variable already captures the base path prefix)
        html = html.replace("</head>", STATIC_SHIM + "\n</head>")
        dest = output / filepath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        return True

    def write_json(url: str, filepath: str) -> bool:
        resp = client.get(url)
        if resp.status_code != 200:
            return False
        dest = output / filepath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(resp.text, encoding="utf-8")
        return True

    # --- HTML: Root pages ---
    print("\nGenerating HTML pages...")
    write_html("/", "index.html")
    write_html("/search", "search/index.html")
    write_html("/hierarchy", "hierarchy/index.html")
    write_html("/methodology", "methodology/index.html")
    write_html("/cpi", "cpi/index.html")
    print("  5 root pages")

    # --- HTML: CPI member pages ---
    cpi_member_codes = []
    with contextlib.suppress(Exception):
        cpi_member_codes = [
            r[0]
            for r in db.execute("SELECT member_code FROM dim_cpi_member ORDER BY member_code").fetchall()
        ]
    if cpi_member_codes:
        t0_cpi = time.time()
        for i, mc in enumerate(cpi_member_codes, 1):
            write_html(f"/cpi/member/{mc}", f"cpi/member/{mc}/index.html")
            if i % 100 == 0:
                elapsed = time.time() - t0_cpi
                rate = i / elapsed
                remaining = (len(cpi_member_codes) - i) / rate
                print(f"  {i}/{len(cpi_member_codes)} CPI member pages ({rate:.0f}/s, ~{remaining:.0f}s left)")
        elapsed = time.time() - t0_cpi
        print(f"  {len(cpi_member_codes)} CPI member pages ({elapsed:.1f}s)")

    # --- HTML: Trend pages ---
    write_html("/trends", "trends/index.html")
    write_html("/trends/compare", "trends/compare/index.html")
    write_html("/trends/movers", "trends/movers/index.html")
    trend_page_count = 3
    t0_trends = time.time()
    for i, soc in enumerate(soc_codes, 1):
        write_html(f"/trends/explorer/{soc}", f"trends/explorer/{soc}/index.html")
        write_html(f"/trends/geography/{soc}", f"trends/geography/{soc}/index.html")
        if i % 200 == 0:
            elapsed = time.time() - t0_trends
            rate = i / elapsed
            remaining = (len(soc_codes) - i) / rate
            print(f"  {i}/{len(soc_codes)} trend pages ({rate:.0f}/s, ~{remaining:.0f}s left)")
    trend_page_count += len(soc_codes) * 2
    elapsed = time.time() - t0_trends
    print(f"  {trend_page_count} trend pages ({elapsed:.1f}s)")

    # --- HTML: Lesson pages ---
    from jobclass.web.lessons import LESSON_SLUGS

    write_html("/lessons", "lessons/index.html")
    for slug in LESSON_SLUGS:
        write_html(f"/lessons/{slug}", f"lessons/{slug}/index.html")
    print(f"  {1 + len(LESSON_SLUGS)} lesson pages")

    # 404 page (GitHub Pages convention)
    resp = client.get("/this-page-does-not-exist-404")
    if resp.status_code == 404:
        html = resp.text
        if bp:
            html = rewrite_paths(html, bp)
        html = html.replace("</head>", STATIC_SHIM + "\n</head>")
        (output / "404.html").write_text(html, encoding="utf-8")
        print("  404 error page")

    # --- HTML: Occupation pages ---
    t0 = time.time()
    for i, soc in enumerate(soc_codes, 1):
        write_html(f"/occupation/{soc}", f"occupation/{soc}/index.html")
        write_html(f"/occupation/{soc}/wages", f"occupation/{soc}/wages/index.html")
        if i % 200 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            remaining = (len(soc_codes) - i) / rate
            print(f"  {i}/{len(soc_codes)} occupations ({rate:.0f}/s, ~{remaining:.0f}s left)")
    elapsed = time.time() - t0
    print(f"  {len(soc_codes)} occupation pages ({elapsed:.1f}s)")

    # --- JSON: Global API endpoints ---
    print("\nGenerating API JSON files...")
    global_apis = [
        ("/api/stats", "api/stats.json"),
        ("/api/health", "api/health.json"),
        ("/api/metadata", "api/metadata.json"),
        ("/api/geographies", "api/geographies.json"),
        ("/api/methodology/sources", "api/methodology/sources.json"),
        ("/api/methodology/validation", "api/methodology/validation.json"),
        ("/api/occupations/hierarchy", "api/occupations/hierarchy.json"),
        ("/api/trends/metrics", "api/trends/metrics.json"),
        ("/api/trends/movers", "api/trends/movers.json"),  # default (latest year)
    ]
    for url, filepath in global_apis:
        write_json(url, filepath)
    print(f"  {len(global_apis)} global endpoints")

    # Per-year and per-metric movers files
    movers_metrics = [
        "employment_count",
        "mean_annual_wage",
        "median_annual_wage",
        "real_mean_annual_wage",
        "real_median_annual_wage",
    ]
    movers_years = db.execute("""
        SELECT DISTINCT tp.year
        FROM fact_derived_series d
        JOIN dim_time_period tp ON d.period_key = tp.period_key
        JOIN dim_metric m ON d.metric_key = m.metric_key
        WHERE m.metric_name = 'yoy_percent_change'
        ORDER BY tp.year
    """).fetchall()
    movers_count = 0
    for met in movers_metrics:
        suffix = "" if met == "employment_count" else f"_{met}"
        write_json(f"/api/trends/movers?metric={met}", f"api/trends/movers{suffix}.json")
        movers_count += 1
        for (yr,) in movers_years:
            write_json(f"/api/trends/movers?year={yr}&metric={met}", f"api/trends/movers-{yr}{suffix}.json")
            movers_count += 1
    print(f"  {movers_count} movers files ({len(movers_metrics)} metrics x {len(movers_years)} years + defaults)")

    # Search index — built directly from DB since the API rejects empty queries
    search_rows = db.execute("""
        SELECT soc_code, occupation_title, occupation_level, occupation_level_name
        FROM dim_occupation
        WHERE is_current = true
        ORDER BY soc_code
    """).fetchall()
    search_data = {
        "results": [
            {
                "soc_code": r[0],
                "occupation_title": r[1],
                "occupation_level": r[2],
                "occupation_level_name": r[3],
            }
            for r in search_rows
        ],
        "total": len(search_rows),
        "limit": len(search_rows),
        "offset": 0,
    }
    search_dest = output / "api" / "occupations" / "search.json"
    search_dest.parent.mkdir(parents=True, exist_ok=True)
    search_dest.write_text(json.dumps(search_data), encoding="utf-8")
    print(f"  Search index ({len(search_rows)} occupations)")

    # --- JSON: Per-occupation endpoints ---
    t0 = time.time()
    json_count = 0
    for i, soc in enumerate(soc_codes, 1):
        endpoints = [
            (f"/api/occupations/{soc}", f"api/occupations/{soc}.json"),
            (f"/api/occupations/{soc}/wages?geo_type=national", f"api/occupations/{soc}/wages-national.json"),
            (f"/api/occupations/{soc}/wages?geo_type=state", f"api/occupations/{soc}/wages-state.json"),
            (f"/api/occupations/{soc}/skills", f"api/occupations/{soc}/skills.json"),
            (f"/api/occupations/{soc}/knowledge", f"api/occupations/{soc}/knowledge.json"),
            (f"/api/occupations/{soc}/abilities", f"api/occupations/{soc}/abilities.json"),
            (f"/api/occupations/{soc}/activities", f"api/occupations/{soc}/activities.json"),
            (f"/api/occupations/{soc}/education", f"api/occupations/{soc}/education.json"),
            (f"/api/occupations/{soc}/technology", f"api/occupations/{soc}/technology.json"),
            (f"/api/occupations/{soc}/tasks", f"api/occupations/{soc}/tasks.json"),
            (f"/api/occupations/{soc}/projections", f"api/occupations/{soc}/projections.json"),
            (f"/api/occupations/{soc}/similar", f"api/occupations/{soc}/similar.json"),
            (f"/api/trends/{soc}", f"api/trends/{soc}.json"),
            (f"/api/trends/{soc}?metric=mean_annual_wage", f"api/trends/{soc}-mean_annual_wage.json"),
            (f"/api/trends/{soc}?metric=median_annual_wage", f"api/trends/{soc}-median_annual_wage.json"),
            (f"/api/trends/{soc}?metric=real_mean_annual_wage", f"api/trends/{soc}-real_mean_annual_wage.json"),
            (f"/api/trends/{soc}?metric=real_median_annual_wage", f"api/trends/{soc}-real_median_annual_wage.json"),
            (
                f"/api/trends/compare/geography?soc_code={soc}",
                f"api/trends/compare/geography-{soc}.json",
            ),
        ]
        for url, filepath in endpoints:
            if write_json(url, filepath):
                json_count += 1
        if i % 200 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            remaining = (len(soc_codes) - i) / rate
            print(f"  {i}/{len(soc_codes)} occupations ({rate:.0f}/s, ~{remaining:.0f}s left)")
    elapsed = time.time() - t0
    print(f"  {json_count} JSON files for {len(soc_codes)} occupations ({elapsed:.1f}s)")

    # --- JSON: CPI API endpoints ---
    if cpi_member_codes:
        t0_cpi = time.time()
        cpi_json_count = 0
        for i, mc in enumerate(cpi_member_codes, 1):
            cpi_endpoints = [
                (f"/api/cpi/members/{mc}", f"api/cpi/members/{mc}.json"),
                (f"/api/cpi/members/{mc}/children", f"api/cpi/members/{mc}/children.json"),
                (f"/api/cpi/members/{mc}/relations", f"api/cpi/members/{mc}/relations.json"),
                (f"/api/cpi/members/{mc}/siblings", f"api/cpi/members/{mc}/siblings.json"),
                (f"/api/cpi/members/{mc}/variants", f"api/cpi/members/{mc}/variants.json"),
                (f"/api/cpi/members/{mc}/series", f"api/cpi/members/{mc}/series.json"),
            ]
            for url, filepath in cpi_endpoints:
                if write_json(url, filepath):
                    cpi_json_count += 1
            if i % 100 == 0:
                elapsed = time.time() - t0_cpi
                rate = i / elapsed
                remaining = (len(cpi_member_codes) - i) / rate
                print(f"  {i}/{len(cpi_member_codes)} CPI members ({rate:.0f}/s, ~{remaining:.0f}s left)")
        # CPI search index
        cpi_search = db.execute("""
            SELECT member_code, title, hierarchy_level, semantic_role
            FROM dim_cpi_member ORDER BY member_code
        """).fetchall()
        cpi_search_data = {
            "query": "",
            "total": len(cpi_search),
            "results": [
                {"member_code": r[0], "title": r[1], "hierarchy_level": r[2], "semantic_role": r[3]}
                for r in cpi_search
            ],
        }
        cpi_search_dest = output / "api" / "cpi" / "search.json"
        cpi_search_dest.parent.mkdir(parents=True, exist_ok=True)
        cpi_search_dest.write_text(json.dumps(cpi_search_data), encoding="utf-8")
        cpi_json_count += 1
        elapsed = time.time() - t0_cpi
        print(f"  {cpi_json_count} CPI JSON files ({elapsed:.1f}s)")

    # --- .nojekyll (prevent GitHub Pages Jekyll processing) ---
    (output / ".nojekyll").touch()

    # --- Summary ---
    total_files = sum(1 for _ in output.rglob("*") if _.is_file())
    total_size_mb = sum(f.stat().st_size for f in output.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"\nBuild complete: {output}/")
    print(f"  {total_files:,} files, {total_size_mb:.1f} MB")
    if bp:
        print(f"  Base path: {bp}")

    # Clean up shared connection
    reset_db()
    shared_conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build static site for GitHub Pages")
    parser.add_argument(
        "--base-path",
        default="/",
        help="URL base path for GitHub Pages (e.g., /jobclass). Default: /",
    )
    parser.add_argument(
        "--output",
        default="_site",
        help="Output directory (default: _site)",
    )
    args = parser.parse_args()
    build_static(args.base_path, args.output)


if __name__ == "__main__":
    main()
