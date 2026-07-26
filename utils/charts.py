import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

COLORS = px.colors.qualitative.Set2


def bar_chart(df, x, y, title="", color=None, orientation="v", top_n=None):
    data = df.copy()
    if top_n and orientation == "v":
        data = data.nlargest(top_n, y)
    elif top_n and orientation == "h":
        data = data.nlargest(top_n, y)

    fig = px.bar(
        data, x=x, y=y, title=title, color=color,
        orientation=orientation, color_discrete_sequence=COLORS
    )
    fig.update_layout(
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eee")
    return fig


def line_chart(df, x, y, title="", color=None):
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLORS, markers=True
    )
    fig.update_layout(
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eee")
    return fig


def pie_chart(df, names, values, title=""):
    fig = px.pie(
        df, names=names, values=values, title=title,
        color_discrete_sequence=COLORS
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
    return fig


def horizontal_bar(df, x, y, title="", top_n=10):
    df_plot = df.nlargest(top_n, x).copy()
    fig = px.bar(
        df_plot, x=x, y=y, title=title, orientation="h",
        color_discrete_sequence=COLORS
    )
    fig.update_layout(
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
        showlegend=False,
        yaxis=dict(autorange="reversed"),
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eee")
    fig.update_yaxes(showgrid=False)
    return fig


def heatmap_chart(df, x, y, z, title=""):
    fig = px.density_heatmap(
        df, x=x, y=y, z=z, color_continuous_scale="YlOrRd",
        title=title
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
    return fig


def dual_axis_chart(df, x, y1, y2, title="", y1_label="", y2_label=""):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x], y=df[y1], name=y1.replace("_", " ").title(),
        marker_color="#63c7e8", yaxis="y"
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y2], name=y2.replace("_", " ").title(),
        mode="lines+markers", line=dict(color="#e8505b", width=2),
        yaxis="y2"
    ))
    fig.update_layout(
        title=title,
        yaxis=dict(title=y1_label or y1.replace("_", " ").title()),
        yaxis2=dict(title=y2_label or y2.replace("_", " ").title(), overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor="white",
    )
    return fig
