import pandas as pd


def format_currency(value, symbol="$"):
    if pd.isna(value) or value is None:
        return "-"
    return f"{symbol}{value:,.2f}"


def format_currency_short(value, symbol="$"):
    if pd.isna(value) or value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"{symbol}{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"{symbol}{value / 1_000:,.1f}K"
    return f"{symbol}{value:,.2f}"


def format_number(value):
    if pd.isna(value) or value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def format_number_full(value):
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:,.0f}"


def format_percentage(value):
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:.1f}%"


def format_date_range(start_date, end_date):
    if start_date is None or end_date is None:
        return "-"
    return f"{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"


def format_delta(value):
    if value is None or pd.isna(value):
        return None
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"
