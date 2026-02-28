import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

st.set_page_config(page_title="Zomato Delivery Intelligence Dashboard", layout="wide")

THEME_CONFIGS = {
    "light": {
        "template": "plotly_white",
        "mapbox_style": "positron",
        "background": "#F1F5F9",
        "surface": "#FFFFFF",
        "text_primary": "#1E293B",
        "text_muted": "#64748B",
        "accent": "#2563EB",
        "border": "#CBD5E1",
        "filter_hover_bg": "#E5E7EB",
        "paper_bg": "#FFFFFF",
        "plot_bg": "#FFFFFF",
        "font_color": "#1E293B",
        "gridcolor": "rgba(203, 213, 225, 0.5)",
        "hover_bg": "#FFFFFF",
        "marker_line": "#FFFFFF",
        "trend_fill": "rgba(37, 99, 235, 0.2)",
        "semantic": {
            "optimal": "#059669",
            "average": "#0891B2",
            "warning": "#D97706",
            "critical": "#DC2626",
            "neutral": "#475569",
        },
    },
}


def get_theme_config():
    return THEME_CONFIGS["light"]


def get_mapbox_style_for_theme():
    return "carto-positron"


def semantic_bucket(label):
    label_text = str(label).strip().lower()
    if any(term in label_text for term in ["sunny", "clear", "low", "optimal", "fast"]):
        return "optimal"
    if any(term in label_text for term in ["cloudy", "moderate", "medium", "stable", "normal"]):
        return "average"
    if any(term in label_text for term in ["rain", "high", "warning", "slow"]):
        return "warning"
    if any(term in label_text for term in ["storm", "jam", "critical", "severe", "heavy"]):
        return "critical"
    return "neutral"


def semantic_color_for_label(label, config):
    return config["semantic"][semantic_bucket(label)]


def get_data_palette(config):
    semantic = config["semantic"]
    return [
        semantic["optimal"],
        semantic["average"],
        semantic["warning"],
        semantic["critical"],
        semantic["neutral"],
        config["accent"],
    ]


def apply_plotly_defaults_for_theme():
    config = get_theme_config()
    px.defaults.template = config["template"]
    px.defaults.color_discrete_sequence = get_data_palette(config)


def apply_app_theme():
    config = get_theme_config()
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {config['background']};
                color: {config['text_primary']};
            }}

            [data-testid="stHeader"] {{
                background: transparent;
            }}

            [data-testid="stSidebar"] {{
                background-color: {config['surface']};
                border-right: 1px solid {config['border']};
            }}

            [data-testid="stSidebar"] * {{
                color: {config['text_primary']};
            }}

            [data-testid="stMetric"] {{
                background-color: {config['surface']};
                border: 1px solid {config['border']};
                border-radius: 12px;
                padding: 0.75rem;
            }}

            [data-testid="stMetricLabel"] {{
                color: {config['text_muted']};
            }}

            [data-testid="stMetricValue"] {{
                color: {config['text_primary']};
            }}

            .stTextInput > div > div > input,
            .stSelectbox > div > div,
            .stMultiSelect > div > div,
            .stNumberInput > div > div > input,
            .stDateInput > div > div > input,
            .stSlider > div,
            [data-testid="stExpander"] {{
                background-color: {config['surface']};
                color: {config['text_primary']};
                border: 1px solid {config['border']};
                border-radius: 10px;
            }}

            [data-testid="stSidebar"] [data-testid="stExpander"] details summary:hover {{
                background-color: {config['filter_hover_bg']};
            }}

            [data-testid="stSidebar"] [data-baseweb="tag"] {{
                background-color: {config['filter_hover_bg']} !important;
                border: 1px solid {config['border']} !important;
                color: {config['text_primary']} !important;
            }}

            [data-testid="stSidebar"] [data-baseweb="tag"] span,
            [data-testid="stSidebar"] [data-baseweb="tag"] svg {{
                color: {config['text_primary']} !important;
                fill: {config['text_primary']} !important;
            }}

            [data-testid="stSidebar"] [role="option"][aria-selected="true"] {{
                background-color: {config['filter_hover_bg']} !important;
                color: {config['text_primary']} !important;
            }}

            .stButton > button,
            .stDownloadButton > button {{
                border: 1px solid {config['border']};
                background-color: {config['surface']};
                color: {config['text_primary']};
                border-radius: 10px;
            }}

            .stButton > button:hover,
            .stDownloadButton > button:hover {{
                border-color: {config['accent']};
                color: {config['accent']};
            }}

            .stButton > button[kind="primary"] {{
                background-color: {config['accent']};
                color: {config['surface']};
                border-color: {config['accent']};
            }}

            [data-testid="stDataFrame"],
            [data-testid="stTable"] {{
                border: 1px solid {config['border']};
                border-radius: 10px;
                overflow: hidden;
            }}

            [data-testid="stPlotlyChart"] {{
                border: 1px solid {config['border']};
                border-radius: 10px;
                overflow: hidden;
                background-color: {config['surface']};
            }}

            [data-testid="stPlotlyChart"] > div {{
                border-radius: 10px;
                overflow: hidden;
            }}

            h1, h2, h3, h4, h5, h6 {{
                color: {config['text_primary']};
            }}

            p, label, span, small, [data-testid="stCaptionContainer"] {{
                color: {config['text_muted']};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _cycle_colors(count, palette):
    if count <= 0:
        return []
    return [palette[i % len(palette)] for i in range(count)]


def apply_compact_chart_theme(fig):
    config = get_theme_config()
    palette = get_data_palette(config)
    secondary_text = config["text_muted"]

    fig.update_layout(
        template=config["template"],
        colorway=palette,
        paper_bgcolor=config["paper_bg"],
        plot_bgcolor=config["plot_bg"],
        font=dict(color=config["font_color"]),
        hoverlabel=dict(
            font_size=12,
            bgcolor=config["hover_bg"],
            font_color=config["font_color"],
        ),
        xaxis=dict(
            tickfont=dict(color=secondary_text),
            title=dict(font=dict(color=secondary_text)),
        ),
        yaxis=dict(
            tickfont=dict(color=secondary_text),
            title=dict(font=dict(color=secondary_text)),
        ),
    )

    for axis_name in ["xaxis", "yaxis"]:
        if axis_name in fig.layout:
            fig.layout[axis_name].showgrid = True
            fig.layout[axis_name].gridcolor = config["gridcolor"]
            fig.layout[axis_name].zeroline = False

    fig.update_xaxes(tickfont_color=secondary_text, title_font_color=secondary_text)
    fig.update_yaxes(tickfont_color=secondary_text, title_font_color=secondary_text)

    if "mapbox" in fig.layout:
        fig.update_layout(mapbox_style=get_mapbox_style_for_theme())

    if len(fig.data) == 1 and getattr(fig.data[0], "type", None) == "bar":
        trace = fig.data[0]
        values = trace.x if trace.x is not None else trace.y
        count = len(values) if values is not None else 0
        if count > 1:
            trace.marker = dict(
                color=[semantic_color_for_label(value, config) for value in values],
                line=dict(width=0.5, color=config["marker_line"]),
            )

    if len(fig.data) == 1 and getattr(fig.data[0], "type", None) == "histogram":
        fig.data[0].marker = dict(
            color=config["semantic"]["neutral"],
            line=dict(width=0.5, color=config["marker_line"]),
        )

    for trace in fig.data:
        if getattr(trace, "type", None) == "pie" and getattr(trace, "labels", None) is not None:
            trace.marker = dict(
                colors=[semantic_color_for_label(label, config) for label in trace.labels],
                line=dict(width=1, color=config["marker_line"]),
            )

        if getattr(trace, "type", None) == "scatter" and "lines" in str(getattr(trace, "mode", "")):
            if trace.line is None or trace.line.color is None:
                trace.line = dict(color=config["accent"], width=2.5)
            if getattr(trace, "fill", None) not in [None, "none"] and (
                trace.fillcolor is None or trace.fillcolor == ""
            ):
                trace.fillcolor = config["trend_fill"]

    return fig


_original_plotly_chart = st.plotly_chart


def themed_plotly_chart(figure_or_data, **kwargs):
    if hasattr(figure_or_data, "update_layout"):
        figure_or_data = apply_compact_chart_theme(figure_or_data)
    return _original_plotly_chart(figure_or_data, **kwargs)


st.plotly_chart = themed_plotly_chart
apply_plotly_defaults_for_theme()

REQUIRED_COLUMNS = {
    "ID",
    "Delivery_person_ID",
    "Delivery_person_Age",
    "Delivery_person_Ratings",
    "Restaurant_latitude",
    "Restaurant_longitude",
    "Delivery_location_latitude",
    "Delivery_location_longitude",
    "Order_Date",
    "Time_Orderd",
    "Time_Order_picked",
    "Weather_conditions",
    "Road_traffic_density",
    "Vehicle_condition",
    "Type_of_order",
    "Type_of_vehicle",
    "multiple_deliveries",
    "Festival",
    "City",
    "Time_taken (min)",
}


def haversine_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        np.radians, [lat1, lon1, lat2, lon2]
    )
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    return radius * c


@st.cache_data(show_spinner=False)
def load_and_prepare_data(file_path, on_time_threshold):
    df = pd.read_csv(file_path)
    df.columns = [col.strip() for col in df.columns]

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        return None, sorted(missing_columns)

    obj_cols = df.select_dtypes(include=["object"]).columns
    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip()

    df = df.replace(
        {
            "NaN": np.nan,
            "nan": np.nan,
            "NaN ": np.nan,
            "": np.nan,
            "None": np.nan,
        }
    )

    numeric_cols = [
        "Delivery_person_Age",
        "Delivery_person_Ratings",
        "Restaurant_latitude",
        "Restaurant_longitude",
        "Delivery_location_latitude",
        "Delivery_location_longitude",
        "Vehicle_condition",
        "multiple_deliveries",
        "Time_taken (min)",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Order_Date"] = pd.to_datetime(
        df["Order_Date"], format="%d-%m-%y", errors="coerce"
    )

    ordered_dt = pd.to_datetime(df["Time_Orderd"], format="%H:%M", errors="coerce")
    picked_dt = pd.to_datetime(df["Time_Order_picked"], format="%H:%M", errors="coerce")
    df["order_hour"] = ordered_dt.dt.hour
    df["pickup_hour"] = picked_dt.dt.hour
    df["order_month"] = df["Order_Date"].dt.to_period("M").astype(str)

    df["distance_km"] = haversine_distance(
        df["Restaurant_latitude"],
        df["Restaurant_longitude"],
        df["Delivery_location_latitude"],
        df["Delivery_location_longitude"],
    )
    df.loc[np.isinf(df["distance_km"]), "distance_km"] = np.nan

    bins = [-np.inf, 5, 10, np.inf]
    labels = ["Short (<5 km)", "Medium (5-10 km)", "Long (>10 km)"]
    df["distance_category"] = pd.cut(df["distance_km"], bins=bins, labels=labels)

    df["is_delayed"] = (df["Time_taken (min)"] > on_time_threshold).astype(int)
    df["is_on_time"] = 1 - df["is_delayed"]

    return df, []


@st.cache_resource(show_spinner=False)
def train_predictive_models(_df):
    feature_cols = [
        "Weather_conditions",
        "Road_traffic_density",
        "City",
        "Festival",
        "Vehicle_condition",
        "Type_of_order",
        "Type_of_vehicle",
        "multiple_deliveries",
        "Delivery_person_Ratings",
        "Delivery_person_Age",
        "distance_km",
    ]

    model_df = _df[feature_cols + ["Time_taken (min)", "is_delayed"]].copy()
    model_df = model_df.dropna(subset=["Time_taken (min)"])

    X = model_df[feature_cols]
    y_reg = model_df["Time_taken (min)"]
    y_cls = model_df["is_delayed"]

    categorical_cols = [
        "Weather_conditions",
        "Road_traffic_density",
        "City",
        "Festival",
        "Type_of_order",
        "Type_of_vehicle",
    ]
    numeric_cols = [
        "Vehicle_condition",
        "multiple_deliveries",
        "Delivery_person_Ratings",
        "Delivery_person_Age",
        "distance_km",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical_cols,
            ),
            (
                "num",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_cols,
            ),
        ]
    )

    X_train, X_test, y_reg_train, y_reg_test = train_test_split(
        X, y_reg, test_size=0.2, random_state=42
    )
    _, _, y_cls_train, y_cls_test = train_test_split(
        X, y_cls, test_size=0.2, random_state=42
    )

    reg_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200, random_state=42, n_jobs=-1, max_depth=14
                ),
            ),
        ]
    )

    cls_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=250,
                    random_state=42,
                    n_jobs=-1,
                    max_depth=14,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    reg_pipeline.fit(X_train, y_reg_train)
    cls_pipeline.fit(X_train, y_cls_train)

    reg_pred = reg_pipeline.predict(X_test)
    cls_pred = cls_pipeline.predict(X_test)

    r2 = r2_score(y_reg_test, reg_pred)
    mae = mean_absolute_error(y_reg_test, reg_pred)
    cm = confusion_matrix(y_cls_test, cls_pred)

    reg_preprocessor = reg_pipeline.named_steps["preprocessor"]
    reg_model = reg_pipeline.named_steps["model"]
    reg_feature_names = reg_preprocessor.get_feature_names_out()
    reg_importances = pd.DataFrame(
        {
            "feature": reg_feature_names,
            "importance": reg_model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    cls_preprocessor = cls_pipeline.named_steps["preprocessor"]
    cls_model = cls_pipeline.named_steps["model"]
    cls_feature_names = cls_preprocessor.get_feature_names_out()
    cls_importances = pd.DataFrame(
        {
            "feature": cls_feature_names,
            "importance": cls_model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    return {
        "reg_pipeline": reg_pipeline,
        "cls_pipeline": cls_pipeline,
        "r2": r2,
        "mae": mae,
        "confusion_matrix": cm,
        "reg_importances": reg_importances,
        "cls_importances": cls_importances,
    }


def metric_card_row(metrics):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label=label, value=value)


def sampled_df(df, n=5000):
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=42)


def executive_overview_page(df, on_time_threshold):
    st.subheader("Executive Overview")

    total_orders = len(df)
    avg_delivery_time = df["Time_taken (min)"].mean()
    on_time_pct = df["is_on_time"].mean() * 100
    avg_rating = df["Delivery_person_Ratings"].mean()
    avg_age = df["Delivery_person_Age"].mean()
    active_riders = df["Delivery_person_ID"].nunique()
    festival_orders_pct = (df["Festival"].eq("Yes").mean()) * 100
    non_festival_orders_pct = 100 - festival_orders_pct

    metric_card_row(
        {
            "Total Orders": f"{total_orders:,}",
            "Average Delivery Time": f"{avg_delivery_time:.2f} min",
            f"On-Time % (<={on_time_threshold} min)": f"{on_time_pct:.2f}%",
            "Average Rider Rating": f"{avg_rating:.2f}",
        }
    )
    metric_card_row(
        {
            "Average Rider Age": f"{avg_age:.1f} yrs",
            "Total Active Riders": f"{active_riders:,}",
            "Festival Orders %": f"{festival_orders_pct:.2f}%",
            "Non-Festival Orders %": f"{non_festival_orders_pct:.2f}%",
        }
    )

    col1, col2 = st.columns(2)
    with col1:
        trend = (
            df.dropna(subset=["Order_Date"]) 
            .groupby("Order_Date", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        fig = px.line(trend, x="Order_Date", y="orders", title="Orders Trend (by Date)")
        st.plotly_chart(fig, use_container_width=True)

        city_orders = (
            df.groupby("City", dropna=False, as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("orders", ascending=False)
        )
        fig = px.bar(city_orders, x="City", y="orders", title="Orders by City")
        st.plotly_chart(fig, use_container_width=True)

        weather_orders = (
            df.groupby("Weather_conditions", dropna=False, as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("orders", ascending=False)
        )
        fig = px.bar(
            weather_orders,
            x="Weather_conditions",
            y="orders",
            title="Orders by Weather Condition",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            df,
            x="Time_taken (min)",
            nbins=40,
            title="Delivery Time Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

        traffic_orders = (
            df.groupby("Road_traffic_density", dropna=False, as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("orders", ascending=False)
        )
        fig = px.bar(
            traffic_orders,
            x="Road_traffic_density",
            y="orders",
            title="Orders by Traffic Density",
        )
        st.plotly_chart(fig, use_container_width=True)

        weekly_on_time = (
            df.dropna(subset=["Order_Date"])
            .assign(week_start=lambda d: d["Order_Date"].dt.to_period("W").dt.start_time)
            .groupby("week_start", as_index=False)["is_on_time"]
            .mean()
            .sort_values("week_start")
        )
        weekly_on_time["on_time_pct"] = weekly_on_time["is_on_time"] * 100

        if not weekly_on_time.empty:
            on_time_fig = px.line(
                weekly_on_time,
                x="week_start",
                y="on_time_pct",
                markers=True,
                title=f"Weekly On-Time Rate (<= {on_time_threshold} min)",
            )
            on_time_fig.update_yaxes(range=[0, 100], ticksuffix="%")
            on_time_fig.add_hline(
                y=90,
                line_dash="dash",
                annotation_text="Target: 90%",
                annotation_position="bottom right",
            )
            st.plotly_chart(on_time_fig, use_container_width=True)


def delivery_operations_page(df):
    st.subheader("Delivery Operations")

    col1, col2 = st.columns(2)

    with col1:
        city_time = (
            df.groupby("City", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(city_time, x="City", y="Time_taken (min)", title="Avg Delivery Time by City"),
            use_container_width=True,
        )

        weather_time = (
            df.groupby("Weather_conditions", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                weather_time,
                x="Weather_conditions",
                y="Time_taken (min)",
                title="Avg Delivery Time by Weather",
            ),
            use_container_width=True,
        )

        traffic_time = (
            df.groupby("Road_traffic_density", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                traffic_time,
                x="Road_traffic_density",
                y="Time_taken (min)",
                title="Avg Delivery Time by Traffic Density",
            ),
            use_container_width=True,
        )

    with col2:
        vehicle_time = (
            df.groupby("Type_of_vehicle", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                vehicle_time,
                x="Type_of_vehicle",
                y="Time_taken (min)",
                title="Avg Delivery Time by Vehicle Type",
            ),
            use_container_width=True,
        )

        order_type_time = (
            df.groupby("Type_of_order", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                order_type_time,
                x="Type_of_order",
                y="Time_taken (min)",
                title="Avg Delivery Time by Type of Order",
            ),
            use_container_width=True,
        )

        scatter_df = sampled_df(df.dropna(subset=["distance_km", "Time_taken (min)"]), n=8000)
        distance_scatter = px.scatter(
            scatter_df,
            x="distance_km",
            y="Time_taken (min)",
            color="Road_traffic_density",
            title="Distance vs Delivery Time",
            opacity=0.6,
        )
        distance_scatter.update_layout(
            margin=dict(l=12, r=12, t=72, b=110),
            title=dict(y=0.97, pad=dict(b=12)),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.23,
                xanchor="center",
                x=0.5,
                title=None,
            ),
        )
        st.plotly_chart(distance_scatter, use_container_width=True)

    st.markdown("### Distance Analysis")
    col3, col4 = st.columns(2)

    with col3:
        avg_dist_city = (
            df.groupby("City", as_index=False)["distance_km"]
            .mean()
            .sort_values("distance_km", ascending=False)
        )
        st.plotly_chart(
            px.bar(avg_dist_city, x="City", y="distance_km", title="Avg Distance per City"),
            use_container_width=True,
        )

    with col4:
        dist_cat = (
            df.groupby("distance_category", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        distance_category_pie = px.pie(
            dist_cat,
            names="distance_category",
            values="orders",
            title="Distance Category",
        )
        distance_category_pie.update_layout(
            margin=dict(l=12, r=12, t=72, b=98),
            title=dict(y=0.97, pad=dict(b=12)),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.18,
                xanchor="center",
                x=0.5,
                title=None,
            ),
        )
        st.plotly_chart(distance_category_pie, use_container_width=True)


def rider_efficiency_page(df, on_time_threshold):
    st.subheader("Rider Efficiency")

    rider_grp = (
        df.groupby("Delivery_person_ID", as_index=False)
        .agg(
            orders=("ID", "count"),
            avg_delivery_time=("Time_taken (min)", "mean"),
            on_time_pct=("is_on_time", "mean"),
            avg_rating=("Delivery_person_Ratings", "mean"),
            avg_age=("Delivery_person_Age", "mean"),
            avg_multiple_deliveries=("multiple_deliveries", "mean"),
        )
        .dropna(subset=["avg_delivery_time"])
    )
    rider_grp["on_time_pct"] = rider_grp["on_time_pct"] * 100

    def minmax(series):
        if series.max() == series.min():
            return pd.Series(np.ones(len(series)), index=series.index)
        return (series - series.min()) / (series.max() - series.min())

    rating_norm = minmax(rider_grp["avg_rating"])
    ontime_norm = minmax(rider_grp["on_time_pct"])
    time_inv_norm = 1 - minmax(rider_grp["avg_delivery_time"])
    multi_inv_norm = 1 - minmax(rider_grp["avg_multiple_deliveries"])

    rider_grp["efficiency_score"] = (
        100
        * (
            0.35 * rating_norm
            + 0.30 * time_inv_norm
            + 0.25 * ontime_norm
            + 0.10 * multi_inv_norm
        )
    )

    metric_card_row(
        {
            "Total Riders": f"{rider_grp['Delivery_person_ID'].nunique():,}",
            "Avg Orders per Rider": f"{rider_grp['orders'].mean():.2f}",
            "Avg Delivery Time per Rider": f"{rider_grp['avg_delivery_time'].mean():.2f} min",
            f"Avg On-Time % (<= {on_time_threshold} min)": f"{rider_grp['on_time_pct'].mean():.2f}%",
        }
    )
    metric_card_row(
        {
            "Avg Rating per Rider": f"{rider_grp['avg_rating'].mean():.2f}",
            "Avg Multiple Deliveries per Rider": f"{rider_grp['avg_multiple_deliveries'].mean():.2f}",
        }
    )

    col1, col2 = st.columns(2)

    with col1:
        top10 = rider_grp.nlargest(10, "efficiency_score").sort_values("efficiency_score")
        st.plotly_chart(
            px.bar(
                top10,
                x="efficiency_score",
                y="Delivery_person_ID",
                orientation="h",
                title="Top 10 Riders by Efficiency",
            ),
            use_container_width=True,
        )

        st.plotly_chart(
            px.scatter(
                rider_grp,
                x="avg_rating",
                y="avg_delivery_time",
                size="orders",
                title="Delivery Time vs Rider Rating",
                hover_data=["Delivery_person_ID", "efficiency_score"],
            ),
            use_container_width=True,
        )

        orders_by_rider = rider_grp.sort_values("orders", ascending=False).head(30)
        st.plotly_chart(
            px.bar(
                orders_by_rider,
                x="Delivery_person_ID",
                y="orders",
                title="Orders Completed by Rider (Top 30)",
            ),
            use_container_width=True,
        )

    with col2:
        bottom10 = rider_grp.nsmallest(10, "efficiency_score").sort_values("efficiency_score")
        st.plotly_chart(
            px.bar(
                bottom10,
                x="efficiency_score",
                y="Delivery_person_ID",
                orientation="h",
                title="Bottom 10 Riders",
            ),
            use_container_width=True,
        )

        st.plotly_chart(
            px.scatter(
                rider_grp,
                x="avg_age",
                y="avg_delivery_time",
                color="efficiency_score",
                title="Age vs Performance Analysis",
                hover_data=["Delivery_person_ID", "orders"],
            ),
            use_container_width=True,
        )

        st.plotly_chart(
            px.histogram(
                rider_grp,
                x="efficiency_score",
                nbins=30,
                title="Efficiency Score Distribution",
            ),
            use_container_width=True,
        )

    st.markdown("### Rider Ranking Table")
    ranking_table = rider_grp.sort_values("efficiency_score", ascending=False).reset_index(drop=True)
    ranking_table.index = ranking_table.index + 1
    st.dataframe(ranking_table, use_container_width=True)


def demand_time_analysis_page(df):
    st.subheader("Demand & Time Analysis")

    col1, col2 = st.columns(2)

    with col1:
        daily = (
            df.dropna(subset=["Order_Date"]) 
            .groupby("Order_Date", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        st.plotly_chart(
            px.line(daily, x="Order_Date", y="orders", title="Orders per Day"),
            use_container_width=True,
        )

        monthly = (
            df.dropna(subset=["order_month"]) 
            .groupby("order_month", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        st.plotly_chart(
            px.bar(monthly, x="order_month", y="orders", title="Orders per Month"),
            use_container_width=True,
        )

        hour_df = (
            df.dropna(subset=["order_hour"]) 
            .groupby("order_hour", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("order_hour")
        )
        st.plotly_chart(
            px.bar(hour_df, x="order_hour", y="orders", title="Orders per Hour"),
            use_container_width=True,
        )

    with col2:
        peak_hours = (
            df.dropna(subset=["order_hour"]) 
            .groupby("order_hour", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("orders", ascending=False)
            .head(5)
        )
        st.plotly_chart(
            px.bar(peak_hours, x="order_hour", y="orders", title="Peak Order Hours (Top 5)"),
            use_container_width=True,
        )

        festival_cmp = (
            df.groupby("Festival", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        st.plotly_chart(
            px.bar(
                festival_cmp,
                x="Festival",
                y="orders",
                title="Festival vs Normal Day Order Comparison",
            ),
            use_container_width=True,
        )

        city_trend = (
            df.dropna(subset=["Order_Date", "City"]) 
            .groupby(["Order_Date", "City"], as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        st.plotly_chart(
            px.line(
                city_trend,
                x="Order_Date",
                y="orders",
                color="City",
                title="City-wise Demand Trend",
            ),
            use_container_width=True,
        )


def external_impact_page(df, on_time_threshold):
    st.subheader("External Impact Analysis")

    col1, col2 = st.columns(2)

    with col1:
        weather_vs_time = (
            df.groupby("Weather_conditions", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                weather_vs_time,
                x="Weather_conditions",
                y="Time_taken (min)",
                title="Weather vs Delivery Time",
            ),
            use_container_width=True,
        )

        traffic_vs_time = (
            df.groupby("Road_traffic_density", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                traffic_vs_time,
                x="Road_traffic_density",
                y="Time_taken (min)",
                title="Traffic Density vs Delivery Time",
            ),
            use_container_width=True,
        )

    with col2:
        festival_impact = (
            df.groupby("Festival", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        st.plotly_chart(
            px.bar(
                festival_impact,
                x="Festival",
                y="Time_taken (min)",
                title="Festival Impact on Delivery Time",
            ),
            use_container_width=True,
        )

        vehicle_condition_perf = (
            df.groupby("Vehicle_condition", as_index=False)
            .agg(
                avg_delivery_time=("Time_taken (min)", "mean"),
                on_time_pct=("is_on_time", "mean"),
            )
            .sort_values("Vehicle_condition")
        )
        vehicle_condition_perf["on_time_pct"] = vehicle_condition_perf["on_time_pct"] * 100

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=vehicle_condition_perf["Vehicle_condition"],
                y=vehicle_condition_perf["avg_delivery_time"],
                name="Avg Delivery Time",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=vehicle_condition_perf["Vehicle_condition"],
                y=vehicle_condition_perf["on_time_pct"],
                mode="lines+markers",
                name=f"On-Time % (<= {on_time_threshold} min)",
                yaxis="y2",
            )
        )
        fig.update_layout(
            title="Vehicle Condition vs Performance",
            yaxis=dict(title="Avg Delivery Time (min)"),
            yaxis2=dict(title="On-Time %", overlaying="y", side="right"),
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig, use_container_width=True)


def predictive_analytics_page(df):
    st.subheader("Predictive Analytics")

    with st.spinner("Training regression and delay classification models..."):
        model_bundle = train_predictive_models(df)

    metric_card_row(
        {
            "Regression R²": f"{model_bundle['r2']:.4f}",
            "Regression MAE": f"{model_bundle['mae']:.2f} min",
        }
    )

    st.markdown("### Delivery Time Prediction")

    options = {
        "Weather_conditions": sorted(df["Weather_conditions"].dropna().unique().tolist()),
        "Road_traffic_density": sorted(df["Road_traffic_density"].dropna().unique().tolist()),
        "City": sorted(df["City"].dropna().unique().tolist()),
        "Festival": sorted(df["Festival"].dropna().unique().tolist()),
        "Type_of_order": sorted(df["Type_of_order"].dropna().unique().tolist()),
        "Type_of_vehicle": sorted(df["Type_of_vehicle"].dropna().unique().tolist()),
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        weather = st.selectbox("Weather", options["Weather_conditions"])
        traffic = st.selectbox("Traffic Density", options["Road_traffic_density"])
        city = st.selectbox("City", options["City"])
        festival = st.selectbox("Festival", options["Festival"])

    with col2:
        vehicle_condition = st.slider("Vehicle Condition", 0, 3, 2)
        order_type = st.selectbox("Type of Order", options["Type_of_order"])
        vehicle_type = st.selectbox("Type of Vehicle", options["Type_of_vehicle"])

    with col3:
        multiple_deliveries = st.slider("Multiple Deliveries", 0, 3, 1)
        rider_rating = st.slider("Rider Rating", 1.0, 5.0, 4.2, 0.1)
        rider_age = st.slider("Rider Age", 18, 45, 28)
        distance_km = st.slider("Distance (km)", 0.5, 25.0, 7.5, 0.1)

    input_row = pd.DataFrame(
        [
            {
                "Weather_conditions": weather,
                "Road_traffic_density": traffic,
                "City": city,
                "Festival": festival,
                "Vehicle_condition": vehicle_condition,
                "Type_of_order": order_type,
                "Type_of_vehicle": vehicle_type,
                "multiple_deliveries": multiple_deliveries,
                "Delivery_person_Ratings": rider_rating,
                "Delivery_person_Age": rider_age,
                "distance_km": distance_km,
            }
        ]
    )

    pred_time = model_bundle["reg_pipeline"].predict(input_row)[0]
    delay_prob = model_bundle["cls_pipeline"].predict_proba(input_row)[0][1] * 100

    metric_card_row(
        {
            "Predicted Delivery Time": f"{pred_time:.2f} min",
            "Delay Probability": f"{delay_prob:.2f}%",
        }
    )

    st.markdown("### Delay Classification Model")

    cm = model_bundle["confusion_matrix"]
    cm_df = pd.DataFrame(
        cm,
        index=["Actual On-Time", "Actual Delayed"],
        columns=["Predicted On-Time", "Predicted Delayed"],
    )
    st.plotly_chart(
        px.imshow(cm_df, text_auto=True, title="Confusion Matrix", aspect="auto"),
        use_container_width=True,
    )

    col4, col5 = st.columns(2)
    with col4:
        st.plotly_chart(
            px.bar(
                model_bundle["reg_importances"].head(15),
                x="importance",
                y="feature",
                orientation="h",
                title="Feature Importance (Regression)",
            ),
            use_container_width=True,
        )

    with col5:
        st.plotly_chart(
            px.bar(
                model_bundle["cls_importances"].head(15),
                x="importance",
                y="feature",
                orientation="h",
                title="Feature Importance (Delay Classification)",
            ),
            use_container_width=True,
        )


def location_intelligence_page(df):
    st.subheader("Location Intelligence")

    base_map_df = sampled_df(
        df.dropna(
            subset=[
                "Restaurant_latitude",
                "Restaurant_longitude",
                "Delivery_location_latitude",
                "Delivery_location_longitude",
                "Time_taken (min)",
            ]
        ),
        n=10000,
    )

    col1, col2 = st.columns(2)

    with col1:
        density_fig = px.scatter_mapbox(
            base_map_df,
            lat="Restaurant_latitude",
            lon="Restaurant_longitude",
            color="City",
            zoom=4,
            height=440,
            title="Delivery Density Map",
            mapbox_style="open-street-map",
        )
        density_fig.update_layout(margin=dict(l=0, r=0, t=48, b=0))
        st.plotly_chart(density_fig, use_container_width=True)

        delay_zones = base_map_df[base_map_df["is_delayed"] == 1]
        delay_fig = px.scatter_mapbox(
            delay_zones,
            lat="Delivery_location_latitude",
            lon="Delivery_location_longitude",
            color="Time_taken (min)",
            zoom=4,
            height=440,
            title="High Delay Zones",
            mapbox_style="open-street-map",
        )
        delay_fig.update_layout(margin=dict(l=0, r=0, t=48, b=0))
        st.plotly_chart(delay_fig, use_container_width=True)

    with col2:
        grid_df = base_map_df.copy()
        grid_df["grid_lat"] = grid_df["Restaurant_latitude"].round(2)
        grid_df["grid_lon"] = grid_df["Restaurant_longitude"].round(2)
        avg_map = (
            grid_df.groupby(["grid_lat", "grid_lon"], as_index=False)
            .agg(avg_time=("Time_taken (min)", "mean"), orders=("ID", "count"))
            .sort_values("orders", ascending=False)
        )

        avg_time_map = px.scatter_mapbox(
            avg_map,
            lat="grid_lat",
            lon="grid_lon",
            size="orders",
            color="avg_time",
            zoom=4,
            height=440,
            title="Avg Delivery Time Map",
            mapbox_style="open-street-map",
        )
        avg_time_map.update_layout(margin=dict(l=0, r=0, t=48, b=0))
        st.plotly_chart(avg_time_map, use_container_width=True)

        rest_points = base_map_df[["Restaurant_latitude", "Restaurant_longitude"]].rename(
            columns={"Restaurant_latitude": "lat", "Restaurant_longitude": "lon"}
        )
        rest_points["point_type"] = "Restaurant"

        del_points = base_map_df[["Delivery_location_latitude", "Delivery_location_longitude"]].rename(
            columns={"Delivery_location_latitude": "lat", "Delivery_location_longitude": "lon"}
        )
        del_points["point_type"] = "Delivery"

        dist_points = pd.concat([rest_points, del_points], ignore_index=True)
        dist_map = px.scatter_mapbox(
            dist_points,
            lat="lat",
            lon="lon",
            color="point_type",
            zoom=4,
            height=440,
            title="Order Distribution Map",
            mapbox_style="open-street-map",
        )
        dist_map.update_layout(margin=dict(l=0, r=0, t=48, b=0))
        st.plotly_chart(dist_map, use_container_width=True)


def render_sidebar_filters(df, current_threshold):
    st.sidebar.markdown("### 🔎 Filters")
    st.sidebar.caption("Refine the dashboard view quickly.")

    city_options = sorted(df["City"].dropna().unique().tolist())
    weather_options = sorted(df["Weather_conditions"].dropna().unique().tolist())
    traffic_options = sorted(df["Road_traffic_density"].dropna().unique().tolist())

    time_min = int(np.floor(df["Time_taken (min)"].dropna().min()))
    time_max = int(np.ceil(df["Time_taken (min)"].dropna().max()))

    if "selected_cities" not in st.session_state:
        st.session_state.selected_cities = city_options
    if "selected_weather" not in st.session_state:
        st.session_state.selected_weather = weather_options
    if "selected_traffic" not in st.session_state:
        st.session_state.selected_traffic = traffic_options
    if "selected_time_range" not in st.session_state:
        st.session_state.selected_time_range = (time_min, time_max)
    if "on_time_threshold" not in st.session_state:
        st.session_state.on_time_threshold = current_threshold

    if st.sidebar.button("Reset all filters", use_container_width=True):
        st.session_state.selected_cities = city_options
        st.session_state.selected_weather = weather_options
        st.session_state.selected_traffic = traffic_options
        st.session_state.selected_time_range = (time_min, time_max)
        st.session_state.on_time_threshold = 30
        st.rerun()

    with st.sidebar.expander("⏱ On-Time Threshold", expanded=False):
        selected_threshold = st.slider(
            "On-Time Threshold (min)",
            min_value=20,
            max_value=45,
            key="on_time_threshold",
        )

    if selected_threshold != current_threshold:
        st.rerun()

    with st.sidebar.expander("🌍 Geography", expanded=True):
        st.multiselect(
            "City",
            city_options,
            key="selected_cities",
            placeholder="Choose one or more cities",
        )

    with st.sidebar.expander("🚦 Operating Conditions", expanded=True):
        st.multiselect(
            "Weather",
            weather_options,
            key="selected_weather",
            placeholder="Choose weather conditions",
        )
        st.multiselect(
            "Traffic",
            traffic_options,
            key="selected_traffic",
            placeholder="Choose traffic density",
        )

    with st.sidebar.expander("⏱ Delivery Time", expanded=False):
        st.slider(
            "Time Taken (min)",
            min_value=time_min,
            max_value=time_max,
            key="selected_time_range",
        )

    filtered_df = df[
        df["City"].isin(st.session_state.selected_cities)
        & df["Weather_conditions"].isin(st.session_state.selected_weather)
        & df["Road_traffic_density"].isin(st.session_state.selected_traffic)
        & df["Time_taken (min)"].between(
            st.session_state.selected_time_range[0],
            st.session_state.selected_time_range[1],
        )
    ].copy()

    config = get_theme_config()
    st.sidebar.markdown(
        f"""
        <div style=\"font-size:0.95rem; color:{config['text_muted']}\">
            Matching orders:
            <span style=\"color:{config['accent']}; font-weight:700\">{len(filtered_df):,} / {len(df):,}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return filtered_df


def main():
    st.sidebar.header("Dashboard Controls")
    data_path = st.sidebar.text_input("Dataset path", "Zomato Dataset.csv")
    on_time_threshold = st.session_state.get("on_time_threshold", 30)

    apply_plotly_defaults_for_theme()
    apply_app_theme()

    st.title("Zomato Delivery Intelligence Dashboard")
    st.caption("🎨 Active theme: Light")

    df, missing_columns = load_and_prepare_data(data_path, on_time_threshold)
    if df is None:
        st.error(
            "Missing required columns: " + ", ".join(missing_columns)
        )
        st.stop()

    filtered_df = render_sidebar_filters(df, on_time_threshold)

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    page = st.radio(
        "Navigate",
        [
            "Executive Overview",
            "Delivery Operations",
            "Rider Efficiency",
            "Demand & Time Analysis",
            "External Impact Analysis",
            "Predictive Analytics",
            "Location Intelligence",
        ],
        horizontal=True,
    )

    if page == "Executive Overview":
        executive_overview_page(filtered_df, on_time_threshold)
    elif page == "Delivery Operations":
        delivery_operations_page(filtered_df)
    elif page == "Rider Efficiency":
        rider_efficiency_page(filtered_df, on_time_threshold)
    elif page == "Demand & Time Analysis":
        demand_time_analysis_page(filtered_df)
    elif page == "External Impact Analysis":
        external_impact_page(filtered_df, on_time_threshold)
    elif page == "Predictive Analytics":
        predictive_analytics_page(filtered_df)
    elif page == "Location Intelligence":
        location_intelligence_page(filtered_df)


if __name__ == "__main__":
    main()
