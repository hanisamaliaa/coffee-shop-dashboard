import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

NAVY = "#1C174D"
TEAL = "#0D8A92"
YELLOW = "#FFB703"
RED = "#D9535F"
PURPLE_LIGHT = "#F3F1FA"

CHART_COLORS = [NAVY, TEAL, YELLOW, RED, "#6366F1", "#8B5CF6", "#EC4899", "#F59E0B"]

LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=50, b=30, l=50, r=30),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif"),
)


def _apply_layout(fig, height=380, **kwargs):
    layout = {**LAYOUT_DEFAULTS, "height": height}
    layout.update(kwargs)
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6", zeroline=False)
    return fig


def bar_chart(df, x, y, title="", height=380, color=None):
    fig = px.bar(
        df, x=x, y=y, title=title,
        color=color, color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(showlegend=False if not color else True)
    return _apply_layout(fig, height)


def line_chart(df, x, y, title="", height=380, color=None, markers=True):
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=CHART_COLORS, markers=markers,
    )
    return _apply_layout(fig, height)


def horizontal_bar(df, x, y, title="", height=380, top_n=10):
    data = df.nlargest(top_n, x).copy()
    fig = px.bar(
        data, x=x, y=y, title=title, orientation="h",
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_xaxes(showgrid=True, gridcolor="#F3F4F6")
    fig.update_yaxes(showgrid=False)
    return _apply_layout(fig, height)


def pie_chart(df, names, values, title="", height=380):
    fig = px.pie(
        df, names=names, values=values, title=title,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply_layout(fig, height)


def heatmap_chart(df, x, y, z, title="", height=400):
    fig = px.density_heatmap(
        df, x=x, y=y, z=z,
        color_continuous_scale=[PURPLE_LIGHT, TEAL, NAVY],
        title=title,
    )
    return _apply_layout(fig, height)


def dual_axis_chart(
    df, x, y1, y2, title="", height=380,
    y1_label="", y2_label="",
):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x], y=df[y1], name=y1.replace("_", " ").title(),
        marker_color=TEAL, yaxis="y", opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y2], name=y2.replace("_", " ").title(),
        mode="lines+markers", line=dict(color=YELLOW, width=2.5),
        marker=dict(size=6), yaxis="y2",
    ))
    fig.update_layout(
        title=title,
        yaxis=dict(title=y1_label or y1.replace("_", " ").title()),
        yaxis2=dict(
            title=y2_label or y2.replace("_", " ").title(),
            overlaying="y", side="right",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode="group",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
    return _apply_layout(fig, height)


def area_chart(df, x, y, title="", height=380, color=None):
    fig = px.area(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=CHART_COLORS,
    )
    return _apply_layout(fig, height)
