import json

from plotly.io import to_html

from src.analytics.charts import (
    build_completion_bars, build_daily_trends, build_heatmap,
    build_streaks_bars,
)
from src.analytics.schemas import DashboardResponseSchema, HabitPattern, HeatmapResponseSchema


def render_dashboard_html(
    dashboard: DashboardResponseSchema,
    heatmap: HeatmapResponseSchema,
    patterns: list[HabitPattern],
    year: int,
) -> str:
    all_habits = (
        [h.model_dump(mode="json") for h in dashboard.habits]
        + [h.model_dump(mode="json") for h in dashboard.stale_habits]
    )
    patterns_by_id = {str(p.habit_id): p.model_dump(mode="json") for p in patterns}
    all_days = [{"date": d.date.isoformat(), "value": d.value} for d in heatmap.days]

    fig_heatmap = build_heatmap(all_days, year)
    fig_trends = build_daily_trends(all_days)

    html_heatmap = to_html(fig_heatmap, include_plotlyjs=False, full_html=False)
    html_trends = to_html(fig_trends, include_plotlyjs=False, full_html=False)
    html_completion = (
        to_html(build_completion_bars(all_habits), include_plotlyjs=False, full_html=False)
        if all_habits else ""
    )
    html_streaks = (
        to_html(build_streaks_bars(all_habits), include_plotlyjs=False, full_html=False)
        if all_habits else ""
    )

    cards = "".join(
        _render_habit_card(h, patterns_by_id.get(str(h["habit_id"])))
        for h in all_habits
    )

    js_data = json.dumps({
        "habits": [
            {
                "id": str(h["habit_id"]),
                "title": h["title"],
                "color": h["color_hex"],
                "pattern": patterns_by_id.get(str(h["habit_id"]), {}),
            }
            for h in all_habits
        ],
        "heatmapAll": all_days,
        "year": year,
    }, ensure_ascii=False)

    totals = dashboard.totals
    return _PAGE_TEMPLATE.format(
        plotlyjs_cdn="https://cdn.plot.ly/plotly-2.35.2.min.js",
        heatmap=html_heatmap, trends=html_trends,
        completion=html_completion, streaks=html_streaks,
        cards=cards, total=totals.habits_count,
        active=totals.active_count, stale=totals.stale_count,
        avg=totals.avg_completion_rate, year=year, js_data=js_data,
    )


def _render_habit_card(h: dict, pattern: dict | None) -> str:
    trend = h.get("trend_7d", {}) or {}
    arrow = {"up": "↑", "down": "↓", "flat": "→"}.get(trend.get("direction"), "→")
    shared = " 🤝" if h.get("is_shared") else ""
    stale = " ⚠️" if h.get("is_stale") else ""
    pattern_label = ""
    if pattern and pattern.get("type") not in ("daily", "learning", None):
        pattern_label = f'<div class="habit-pattern">📅 {pattern["label"]}</div>'
    return f"""
    <div class="habit-card" data-habit-id="{h['habit_id']}">
        <div class="habit-header" style="border-left-color: {h['color_hex']};">
            <span class="habit-title">{h['title']}{shared}{stale}</span>
            <span class="habit-rate">{h['completion_rate']:.1f}%</span>
        </div>
        <div class="habit-meta"><span>📅 {h['age_days']} дней</span><span>✓ {h['total_completions']} раз</span></div>
        <div class="habit-meta"><span>🔥 Стрик: {h['current_streak']}</span><span>⭐ Рекорд: {h['best_streak']}</span></div>
        {pattern_label}
        <div class="habit-trend trend-{trend.get('direction', 'flat')}">
            {arrow} {trend.get('delta_pp', 0):+.1f} п.п. за неделю
        </div>
    </div>
    """


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Дашборд аналитики</title>
<script src="{plotlyjs_cdn}"></script>
<style>
    :root {{ --bg:#f6f7f9; --fg:#1f2937; --fg-muted:#6b7280; --card-bg:#fff; --border:#e5e7eb; --primary:#4F46E5; }}
    [data-theme="dark"] {{ --bg:#111827; --fg:#f3f4f6; --fg-muted:#9ca3af; --card-bg:#1f2937; --border:#374151; --primary:#818CF8; }}
    * {{ box-sizing:border-box; }}
    body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--fg); margin:0; padding:24px; transition:background .2s,color .2s; }}
    .container {{ max-width:1200px; margin:0 auto; }}
    .topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; gap:16px; flex-wrap:wrap; }}
    h1 {{ margin:0; font-size:24px; }}
    .controls {{ display:flex; gap:12px; align-items:center; }}
    select,button {{ background:var(--card-bg); color:var(--fg); border:1px solid var(--border); border-radius:8px; padding:8px 14px; font-size:14px; cursor:pointer; }}
    select {{ min-width:200px; }}
    button:hover,select:hover {{ border-color:var(--primary); }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; margin-bottom:20px; }}
    .kpi {{ background:var(--card-bg); border-radius:12px; padding:20px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
    .kpi-value {{ font-size:32px; font-weight:600; color:var(--primary); }}
    .kpi-label {{ font-size:13px; color:var(--fg-muted); margin-top:4px; }}
    .chart-card {{ background:var(--card-bg); border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
    .habits-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }}
    .habit-card {{ background:var(--card-bg); border-radius:12px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.06); cursor:pointer; transition:transform .15s,box-shadow .15s; }}
    .habit-card:hover {{ transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,.1); }}
    .habit-card.selected {{ outline:2px solid var(--primary); }}
    .habit-header {{ display:flex; justify-content:space-between; align-items:center; border-left:4px solid #ccc; padding-left:12px; margin-bottom:12px; }}
    .habit-title {{ font-weight:600; }}
    .habit-rate {{ font-size:20px; font-weight:600; color:var(--primary); }}
    .habit-meta {{ display:flex; justify-content:space-between; font-size:13px; color:var(--fg-muted); margin:6px 0; }}
    .habit-pattern {{ margin-top:8px; font-size:13px; color:var(--fg-muted); }}
    .habit-trend {{ margin-top:10px; padding-top:10px; border-top:1px solid var(--border); font-size:13px; }}
    .trend-up {{ color:#10B981; }} .trend-down {{ color:#EF4444; }} .trend-flat {{ color:var(--fg-muted); }}
</style>
</head>
<body>
<div class="container">
    <div class="topbar">
        <h1>📊 Аналитика привычек</h1>
        <div class="controls">
            <select id="habitFilter"><option value="">Все привычки</option></select>
            <button id="themeToggle">🌙 Тёмная</button>
        </div>
    </div>
    <div class="kpi-grid">
        <div class="kpi"><div class="kpi-value">{total}</div><div class="kpi-label">Всего</div></div>
        <div class="kpi"><div class="kpi-value">{active}</div><div class="kpi-label">Активных</div></div>
        <div class="kpi"><div class="kpi-value">{stale}</div><div class="kpi-label">Заброшенных</div></div>
        <div class="kpi"><div class="kpi-value">{avg:.1f}%</div><div class="kpi-label">Средний %</div></div>
    </div>
    <div class="chart-card">{heatmap}</div>
    <div class="chart-card" id="weekdayCard"></div>
    <div class="chart-card">{trends}</div>
    <div class="chart-card">{completion}</div>
    <div class="chart-card">{streaks}</div>
    <h2 style="margin:24px 0 12px;font-size:18px;">Привычки</h2>
    <div class="habits-grid">{cards}</div>
</div>
<script>
const DATA = {js_data};
const themeBtn = document.getElementById('themeToggle');
function applyTheme(theme) {{
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
    themeBtn.textContent = theme === 'dark' ? '☀️ Светлая' : '🌙 Тёмная';
    const dark = theme === 'dark';
    const layout = {{ paper_bgcolor: dark?'#1f2937':'#fff', plot_bgcolor: dark?'#1f2937':'#fff', 'font.color': dark?'#f3f4f6':'#1f2937' }};
    document.querySelectorAll('.js-plotly-plot').forEach(el => {{ if (el.data) Plotly.relayout(el, layout).catch(()=>{{}}); }});
}}
themeBtn.addEventListener('click', () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
applyTheme(localStorage.getItem('theme') || 'light');

const select = document.getElementById('habitFilter');
DATA.habits.forEach(h => {{
    const opt = document.createElement('option');
    opt.value = h.id; opt.textContent = h.title; select.appendChild(opt);
}});

function renderWeekdayChart(habitId) {{
    const card = document.getElementById('weekdayCard');
    if (!habitId) {{
        card.innerHTML = '<div style="padding:20px;color:var(--fg-muted);">Выберите привычку для паттерна по дням недели</div>';
        return;
    }}
    const habit = DATA.habits.find(h => h.id === habitId);
    if (!habit || !habit.pattern || !habit.pattern.weekday_stats) {{
        card.innerHTML = '<div style="padding:20px;color:var(--fg-muted);">Нет данных</div>';
        return;
    }}
    const byDow = {{}}; habit.pattern.weekday_stats.forEach(s => byDow[s.dow] = s);
    const names = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
    const rates = [1,2,3,4,5,6,7].map(d => (byDow[d]||{{}}).rate || 0);
    const completed = [1,2,3,4,5,6,7].map(d => (byDow[d]||{{}}).completed || 0);
    const colors = rates.map(r => r >= 50 ? '#10B981' : r > 0 ? '#F59E0B' : '#EF4444');
    const dark = document.documentElement.dataset.theme === 'dark';
    const trace = {{
        type:'bar', x:names, y:rates, text:rates.map(r => r.toFixed(0)+'%'), textposition:'auto',
        marker:{{color:colors}}, customdata:completed,
        hovertemplate:'%{{x}}: %{{y:.0f}}% (%{{customdata}} раз)<extra></extra>'
    }};
    const layout = {{
        title: 'Паттерн: ' + habit.title + (habit.pattern.label ? ' (' + habit.pattern.label + ')' : ''),
        yaxis:{{range:[0,100],title:'% выполнения'}}, height:350, margin:{{l:40,r:20,t:40,b:40}},
        paper_bgcolor: dark?'#1f2937':'#fff', plot_bgcolor: dark?'#1f2937':'#fff',
        'font.color': dark?'#f3f4f6':'#1f2937'
    }};
    const plotDiv = document.createElement('div');
    card.innerHTML = ''; card.appendChild(plotDiv);
    Plotly.newPlot(plotDiv, [trace], layout, {{responsive:true}});
}}

document.querySelectorAll('.habit-card').forEach(card => {{
    card.addEventListener('click', () => {{
        const id = card.dataset.habitId;
        select.value = id;
        document.querySelectorAll('.habit-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        renderWeekdayChart(id);
    }});
}});
select.addEventListener('change', () => {{
    document.querySelectorAll('.habit-card').forEach(c => c.classList.remove('selected'));
    renderWeekdayChart(select.value);
}});
renderWeekdayChart('');
</script>
</body>
</html>
"""
