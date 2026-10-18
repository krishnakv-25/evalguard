"""Standalone HTML dashboard reporter for EvalGuard test results."""

import json
from evalguard.models import TestSuiteResult


class HtmlReporter:
    """Generates a responsive, zero-dependency HTML report with interactive filtering."""

    def generate_html(self, result: TestSuiteResult) -> str:
        passed_pct = (result.passed_cases / result.total_cases * 100) if result.total_cases else 0.0
        gate_status_class = "gate-pass" if result.quality_gate_passed else "gate-fail"
        gate_status_text = "QUALITY GATE PASSED" if result.quality_gate_passed else "QUALITY GATE BLOCKED"

        # Serialize test results for client-side search/filter
        test_rows_html = []
        for idx, tr in enumerate(result.results):
            status_class = "status-pass" if (tr.passed and not tr.error) else "status-fail"
            status_label = "PASS" if (tr.passed and not tr.error) else ("ERROR" if tr.error else "FAIL")
            latency_val = f"{tr.response.latency_ms:.0f} ms" if tr.response else "N/A"
            tokens_val = f"{tr.response.total_tokens}" if tr.response else "0"
            content_val = (tr.response.content if tr.response else (tr.error or "No response"))
            cost_val = f"${tr.response.cost_usd:.5f}" if tr.response else "$0.00000"

            guards_html = []
            for gr in tr.guard_results:
                g_badge = "guard-pass" if gr.passed else "guard-fail"
                guards_html.append(f"""
                <div class="guard-pill {g_badge}">
                    <strong>{gr.guard_name}</strong>: {gr.reason} (Score: {gr.score:.2f})
                </div>
                """)

            tags_html = "".join(f'<span class="tag-badge">{t}</span>' for t in tr.tags)

            test_rows_html.append(f"""
            <div class="test-card {status_class}" data-status="{status_label.lower()}" data-tags="{','.join(tr.tags).lower()}">
                <div class="test-header" onclick="toggleDetails('{idx}')">
                    <div class="test-header-left">
                        <span class="badge {status_class}">{status_label}</span>
                        <span class="test-name">{tr.test_case_name}</span>
                        {tags_html}
                    </div>
                    <div class="test-header-right">
                        <span class="meta-item">⏱️ {latency_val}</span>
                        <span class="meta-item">🎯 Score: {tr.overall_score:.2f}</span>
                        <span class="chevron" id="chevron-{idx}">▼</span>
                    </div>
                </div>
                <div class="test-body" id="body-{idx}" style="display: none;">
                    <div class="details-section">
                        <h4>Prompt</h4>
                        <pre class="code-block">{tr.prompt}</pre>
                    </div>
                    <div class="details-section">
                        <h4>Model Response</h4>
                        <pre class="code-block response-block">{content_val}</pre>
                    </div>
                    <div class="details-section">
                        <h4>Guardrail Assertions</h4>
                        <div class="guards-list">
                            {"".join(guards_html)}
                        </div>
                    </div>
                    <div class="details-section meta-grid">
                        <div><strong>Tokens:</strong> {tokens_val}</div>
                        <div><strong>Latency:</strong> {latency_val}</div>
                        <div><strong>Cost:</strong> {cost_val}</div>
                    </div>
                </div>
            </div>
            """)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EvalGuard Report - {result.suite_name}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --surface-hover: #334155;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-yellow: #f59e0b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 32px 20px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{ margin-bottom: 24px; }}
        h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 6px; }}
        .suite-subtitle {{ color: var(--text-muted); font-size: 14px; }}
        
        .gate-banner {{
            padding: 16px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .gate-pass {{ background: rgba(16, 185, 129, 0.15); border: 1px solid var(--accent-green); color: var(--accent-green); }}
        .gate-fail {{ background: rgba(239, 68, 68, 0.15); border: 1px solid var(--accent-red); color: var(--accent-red); }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            padding: 18px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-val {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
        .stat-label {{ color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}

        .toolbar {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
        }}
        .search-box {{
            flex: 1;
            min-width: 250px;
            padding: 10px 14px;
            border-radius: 6px;
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            font-size: 14px;
        }}
        .filter-buttons {{ display: flex; gap: 8px; }}
        .filter-btn {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 8px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }}
        .filter-btn.active {{ background: var(--accent-blue); border-color: var(--accent-blue); }}

        .test-card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
            transition: border-color 0.2s;
        }}
        .test-card:hover {{ border-color: #475569; }}
        .test-header {{
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}
        .test-header-left {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
        .test-header-right {{ display: flex; align-items: center; gap: 16px; color: var(--text-muted); font-size: 13px; }}
        .test-name {{ font-weight: 600; font-size: 15px; }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .status-pass .badge {{ background: var(--accent-green); color: #000; }}
        .status-fail .badge {{ background: var(--accent-red); color: #fff; }}
        .tag-badge {{
            background: rgba(59, 130, 246, 0.2);
            color: var(--accent-blue);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        }}
        .chevron {{ transition: transform 0.2s; font-size: 11px; }}

        .test-body {{
            border-top: 1px solid var(--border-color);
            padding: 18px;
            background: #141e30;
        }}
        .details-section {{ margin-bottom: 16px; }}
        .details-section h4 {{ font-size: 13px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; }}
        .code-block {{
            background: #090d16;
            border: 1px solid var(--border-color);
            padding: 12px;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-break: break-word;
            color: #e2e8f0;
            max-height: 250px;
            overflow-y: auto;
        }}
        .response-block {{ color: #a5f3fc; }}
        .guard-pill {{
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .guard-pass {{ background: rgba(16, 185, 129, 0.12); border-left: 4px solid var(--accent-green); }}
        .guard-fail {{ background: rgba(239, 68, 68, 0.15); border-left: 4px solid var(--accent-red); color: #fca5a5; }}
        .meta-grid {{ display: flex; gap: 24px; color: var(--text-muted); font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>EvalGuard Report</h1>
            <div class="suite-subtitle">Suite: <strong>{result.suite_name}</strong> &bull; Completed in {result.duration_ms / 1000.0:.2f}s</div>
        </header>

        <div class="gate-banner {gate_status_class}">
            <div>🛡️ {gate_status_text}</div>
            <div>Score: {result.average_score:.2f} / 1.00</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val">{result.total_cases}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" style="color: var(--accent-green);">{result.passed_cases}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" style="color: var(--accent-red);">{result.failed_cases}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" style="color: var(--accent-blue);">{passed_pct:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{result.average_score:.2f}</div>
                <div class="stat-label">Avg Quality Score</div>
            </div>
        </div>

        <div class="toolbar">
            <input type="text" id="searchInput" class="search-box" placeholder="Search tests by name or prompt..." onkeyup="filterTests()">
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
                <button class="filter-btn" onclick="setFilter('pass', this)">Passed</button>
                <button class="filter-btn" onclick="setFilter('fail', this)">Failed</button>
                <button class="filter-btn" onclick="setFilter('redteam', this)">Red-Team</button>
            </div>
        </div>

        <div id="testList">
            {"".join(test_rows_html)}
        </div>
    </div>

    <script>
        let currentFilter = 'all';

        function toggleDetails(idx) {{
            const body = document.getElementById('body-' + idx);
            const chevron = document.getElementById('chevron-' + idx);
            if (body.style.display === 'none') {{
                body.style.display = 'block';
                chevron.style.transform = 'rotate(180deg)';
            }} else {{
                body.style.display = 'none';
                chevron.style.transform = 'rotate(0deg)';
            }}
        }}

        function setFilter(filter, btn) {{
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterTests();
        }}

        function filterTests() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.test-card');

            cards.forEach(card => {{
                const status = card.getAttribute('data-status');
                const tags = card.getAttribute('data-tags');
                const text = card.innerText.toLowerCase();

                let matchesFilter = false;
                if (currentFilter === 'all') matchesFilter = true;
                else if (currentFilter === 'pass' && status === 'pass') matchesFilter = true;
                else if (currentFilter === 'fail' && (status === 'fail' || status === 'error')) matchesFilter = true;
                else if (currentFilter === 'redteam' && tags.includes('redteam')) matchesFilter = true;

                const matchesSearch = text.includes(search);
                if (matchesFilter && matchesSearch) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        return html_template

    def write_to_file(self, result: TestSuiteResult, output_path: str) -> None:
        """Writes the HTML report to disk."""
        content = self.generate_html(result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
