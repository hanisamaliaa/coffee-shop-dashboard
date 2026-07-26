import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

COLORS = px.colors.qualitative.Set2


def bar_chart(df, x, y, title="", color=None, orientation="v", top_n=None):
    if top_n and orientation == "v":
        df = df.nlargest(top_n, y)
    elif top_n and orientation == "h":
        df = df.nlargest(top_n, y)

    fig = px.bar(
        df, x=x, y=y, title=title, color=color,
        orientation=orientation, color_discrete_sequence=COLORS
    )
    fig.update_layout(
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20)
    )
    return fig


def line_chart(df, x, y, title="", color=None):
    fig = px.line(
        df, x=x, y=y, title=title, color=color,
        color_discrete_sequence=COLORS, markers=True
    )
    fig.update_layout(
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
        margin=dict(t=40, b=20, l=20, r=20)
    )
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
        margin=dict(t=40, b=20, l=20, r=20)
    )
    return fig


def heatmap_chart(df, x, y, z, title=""):
    fig = px.density_heatmap(
        df, x=x, y=y, z=z, color_continuous_scale="YlOrRd",
        title=title
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20))
    return fig
