from datetime import date, timedelta

import plotly.graph_objects as go


_DOW_NAMES = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}


def build_heatmap(days: list[dict], year: int, title: str = "Календарь активности") -> go.Figure:
    data_by_date = {d["date"]: d["value"] for d in days}
    start = date(year, 1, 1)
    start_of_week = start - timedelta(days=start.weekday())
    end = date(year, 12, 31)
    end_of_week = end + timedelta(days=6 - end.weekday())
    weeks_count = ((end_of_week - start_of_week).days // 7) + 1

    z = [[None] * weeks_count for _ in range(7)]
    text = [[""] * weeks_count for _ in range(7)]
    cur = start_of_week
    for week in range(weeks_count):
        for dow in range(7):
            d = cur + timedelta(days=dow)
            if start <= d <= end:
                val = data_by_date.get(d, 0)
                z[dow][week] = val
                text[dow][week] = f"{d.isoformat()}: {val}"
        cur += timedelta(days=7)

    month_ticks, month_labels = [], []
    cur = start_of_week
    seen_months = set()
    for week in range(weeks_count):
        if cur.day <= 7 and cur.month not in seen_months:
            month_ticks.append(week)
            month_labels.append(cur.strftime("%b"))
            seen_months.add(cur.month)
        cur += timedelta(days=7)

    fig = go.Figure(data=go.Heatmap(
        z=z, text=text, hovertemplate="%{text}<extra></extra>",
        colorscale=[[0, "#ebedf0"], [0.25, "#c6e48b"], [0.5, "#7bc96f"], [0.75, "#239a3b"], [1, "#196127"]],
        showscale=False, xgap=3, ygap=3,
    ))
    fig.update_layout(
        title=title, height=200,
        margin=dict(l=40, r=20, t=40, b=20),
        xaxis=dict(tickmode="array", tickvals=month_ticks, ticktext=month_labels, showgrid=False),
        yaxis=dict(tickmode="array", tickvals=[0, 2, 4, 6], ticktext=["Пн", "Ср", "Пт", "Вс"],
                   autorange="reversed", showgrid=False),
    )
    return fig


def build_completion_bars(habits: list[dict]) -> go.Figure:
    titles = [h["title"] for h in habits]
    rates = [h["completion_rate"] for h in habits]
    fig = go.Figure(data=go.Bar(
        x=titles, y=rates, text=[f"{r:.1f}%" for r in rates], textposition="auto",
        marker_color="#4F46E5", hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(title="Процент выполнения", yaxis=dict(range=[0, 100], title="%"),
                      height=350, margin=dict(l=40, r=20, t=40, b=60))
    return fig


def build_streaks_bars(habits: list[dict]) -> go.Figure:
    titles = [h["title"] for h in habits]
    current = [h["current_streak"] for h in habits]
    best = [h["best_streak"] for h in habits]
    fig = go.Figure(data=[
        go.Bar(name="Текущий", x=titles, y=current, marker_color="#EF4444"),
        go.Bar(name="Рекорд", x=titles, y=best, marker_color="#10B981"),
    ])
    fig.update_layout(title="Серии выполнения", barmode="group", yaxis=dict(title="Дней"),
                      height=350, margin=dict(l=40, r=20, t=40, b=60))
    return fig


def build_daily_trends(days: list[dict]) -> go.Figure:
    if not days:
        fig = go.Figure()
        fig.update_layout(title="Активность по дням", height=300)
        return fig
    dates = [d["date"] for d in days]
    values = [d["value"] for d in days]
    fig = go.Figure(data=go.Scatter(
        x=dates, y=values, mode="lines+markers",
        line=dict(color="#4F46E5", width=2), marker=dict(size=6),
        hovertemplate="%{x|%d %b}: %{y}<extra></extra>",
    ))
    fig.update_layout(title="Активность по дням", yaxis=dict(title="Выполнено"),
                      height=300, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def build_weekday_pattern(stats: list[dict], title: str = "Паттерн по дням недели") -> go.Figure:
    by_dow = {s["dow"]: s for s in stats}
    dows = list(range(1, 8))
    names = [_DOW_NAMES[d] for d in dows]
    rates = [by_dow.get(d, {}).get("rate", 0) for d in dows]
    completed = [by_dow.get(d, {}).get("completed", 0) for d in dows]
    colors = ["#10B981" if r >= 50 else "#F59E0B" if r > 0 else "#EF4444" for r in rates]

    fig = go.Figure(data=go.Bar(
        x=names, y=rates, text=[f"{r:.0f}%" for r in rates], textposition="auto",
        marker_color=colors, customdata=completed,
        hovertemplate="%{x}: %{y:.0f}% (%{customdata} раз)<extra></extra>",
    ))
    fig.update_layout(title=title, yaxis=dict(range=[0, 100], title="% выполнения"),
                      height=350, margin=dict(l=40, r=20, t=40, b=40))
    return fig
