import pandas as pd


def calc_kpi(df):
    if df.empty:
        return {
            "total_revenue": 0,
            "total_transactions": 0,
            "avg_transaction": 0,
            "total_quantity": 0,
        }

    total_revenue = df["total_amount"].sum()
    total_transactions = df["transaction_id"].nunique()
    avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    total_quantity = int(df["quantity"].sum())

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "avg_transaction": avg_transaction,
        "total_quantity": total_quantity,
    }


def calc_delta(df, date_col="timestamp", lookback_months=1):
    if df.empty or date_col not in df.columns:
        return {"revenue": None, "transactions": None, "avg_txn": None, "quantity": None}

    max_date = df[date_col].max()
    cutoff = max_date - pd.DateOffset(months=lookback_months)

    df_curr = df[df[date_col] >= cutoff]
    df_prev = df[df[date_col] < cutoff]

    rev_curr = df_curr["total_amount"].sum()
    rev_prev = df_prev["total_amount"].sum()
    delta_rev = ((rev_curr - rev_prev) / rev_prev * 100) if rev_prev > 0 else None

    txn_curr = df_curr["transaction_id"].nunique()
    txn_prev = df_prev["transaction_id"].nunique()
    delta_txn = ((txn_curr - txn_prev) / txn_prev * 100) if txn_prev > 0 else None

    qty_curr = df_curr["quantity"].sum()
    qty_prev = df_prev["quantity"].sum()
    delta_qty = ((qty_curr - qty_prev) / qty_prev * 100) if qty_prev > 0 else None

    avg_curr = rev_curr / txn_curr if txn_curr > 0 else 0
    avg_prev = rev_prev / txn_prev if txn_prev > 0 else 0
    delta_avg = ((avg_curr - avg_prev) / avg_prev * 100) if avg_prev > 0 else None

    return {
        "revenue": delta_rev,
        "transactions": delta_txn,
        "quantity": delta_qty,
        "avg_txn": delta_avg,
    }


def calc_monthly_data(df):
    if df.empty:
        return pd.DataFrame()

    monthly = (
        df.groupby(df["timestamp"].dt.to_period("M"))
        .agg(
            revenue=("total_amount", "sum"),
            transactions=("transaction_id", "nunique"),
            quantity=("quantity", "sum"),
        )
        .reset_index()
    )
    monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()
    return monthly


def calc_findings(df, monthly_df):
    findings = []
    if df.empty or monthly_df.empty:
        return ["Insufficient data for analysis."]

    top_month = monthly_df.loc[monthly_df["revenue"].idxmax()]
    bot_month = monthly_df.loc[monthly_df["revenue"].idxmin()]

    findings.append(
        f"Highest revenue recorded in <span class='finding-highlight'>{top_month['timestamp'].strftime('%B %Y')}</span> "
        f"with <span class='finding-highlight'>${top_month['revenue']:,.2f}</span>, while the lowest was "
        f"in {bot_month['timestamp'].strftime('%B %Y')} (${bot_month['revenue']:,.2f})."
    )

    cat_rev = (
        df.groupby("product_category")["total_amount"]
        .sum()
        .sort_values(ascending=False)
    )
    top_cat = cat_rev.index[0]
    top_cat_pct = cat_rev.iloc[0] / cat_rev.sum() * 100
    findings.append(
        f"<span class='finding-highlight'>{top_cat}</span> is the dominant product category, "
        f"contributing <span class='finding-highlight'>{top_cat_pct:.1f}%</span> "
        f"(${cat_rev.iloc[0]:,.2f}) of total revenue."
    )

    if "country" in df.columns:
        country_rev = df.groupby("country")["total_amount"].sum().sort_values(ascending=False)
        top_country = country_rev.index[0]
        top_country_pct = country_rev.iloc[0] / country_rev.sum() * 100
        findings.append(
            f"<span class='finding-highlight'>{top_country}</span> leads in revenue generation "
            f"with <span class='finding-highlight'>{top_country_pct:.1f}%</span> "
            f"(${country_rev.iloc[0]:,.2f}) of total revenue."
        )
    elif "store_type" in df.columns:
        store_rev = df.groupby("store_type")["total_amount"].sum().sort_values(ascending=False)
        top_store = store_rev.index[0]
        top_store_pct = store_rev.iloc[0] / store_rev.sum() * 100
        findings.append(
            f"<span class='finding-highlight'>{top_store}</span> store type leads with "
            f"<span class='finding-highlight'>{top_store_pct:.1f}%</span> "
            f"(${store_rev.iloc[0]:,.2f}) of total revenue."
        )

    return findings


def calc_recommendations(df, monthly_df):
    recs = []
    if df.empty or monthly_df.empty:
        return ["Insufficient data for recommendations."]

    top_month = monthly_df.loc[monthly_df["revenue"].idxmax()]
    bot_month = monthly_df.loc[monthly_df["revenue"].idxmin()]

    recs.append(
        f"Maintain momentum during peak periods ({top_month['timestamp'].strftime('%B')}). "
        f"Analyze contributing factors and replicate successful strategies."
    )

    cat_rev = (
        df.groupby("product_category")["total_amount"]
        .sum()
        .sort_values(ascending=False)
    )
    top_cat = cat_rev.index[0]
    recs.append(
        f"Prioritize inventory and marketing for <strong>{top_cat}</strong> category "
        f"which drives {cat_rev.iloc[0] / cat_rev.sum() * 100:.1f}% of total revenue."
    )

    if len(monthly_df) > 1:
        growth = (
            (monthly_df.iloc[-1]["revenue"] - monthly_df.iloc[0]["revenue"])
            / monthly_df.iloc[0]["revenue"]
            * 100
        )
        if growth < 0:
            recs.append(
                f"Revenue trend is declining ({growth:+.1f}% over the period). "
                f"Investigate root causes and implement recovery strategies."
            )
        else:
            recs.append(
                f"Revenue shows positive growth ({growth:+.1f}% over the period). "
                f"Scale successful initiatives across all channels."
            )

    return recs
