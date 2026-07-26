import streamlit as st


def apply_filters(df, options, key_prefix=""):
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='font-size:0.95rem;font-weight:700;color:#1C174D;'>Filters</div>",
        unsafe_allow_html=True,
    )

    date_min = options.get("date_min")
    date_max = options.get("date_max")
    if date_min and date_max:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
            key=f"{key_prefix}_date",
        )
        if len(date_range) == 2:
            df = df[
                (df["timestamp"].dt.date >= date_range[0])
                & (df["timestamp"].dt.date <= date_range[1])
            ]

    filter_mapping = [
        ("country", "Country"),
        ("city", "City"),
        ("store_type", "Store Type"),
        ("product_category", "Product Category"),
        ("payment_method", "Payment Method"),
        ("customer_age_group", "Age Group"),
        ("customer_gender", "Gender"),
    ]

    for col, label in filter_mapping:
        if col in df.columns and options.get(col):
            vals = st.sidebar.multiselect(
                label,
                options=options[col],
                default=[],
                key=f"{key_prefix}_{col}",
            )
            if vals:
                df = df[df[col].isin(vals)]

    return df


def render_filter_sidebar(df, options, key_prefix=""):
    df = apply_filters(df, options, key_prefix)
    return df
