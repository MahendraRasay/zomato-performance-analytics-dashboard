import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

WEATHER_COLOR_MAP = {
    "Fog": "#B0BEC5",
    "Stormy": "#1A237E",
    "Cloudy": "#78909C",
    "Sandstorms": "#C19A6B",
    "Windy": "#42A5F5",
    "Sunny": "#FFB300",
}

AVG_DISTANCE_CITY_COLOR_MAP = {
    "semi-urban": "#5C7C89",
    "semi urban": "#5C7C89",
    "urban": "#1F77B4",
    "metropolitan": "#2C3E50",
    "metropolitian": "#2C3E50",
}

DISTANCE_CATEGORY_COLOR_MAP = {
    "Short (<5 km)": "#2ECC71",
    "Medium (5-10 km)": "#F39C12",
    "Long (>10 km)": "#E74C3C",
}

AVG_DELIVERY_CITY_COLOR_MAP = {
    "urban": "#2ECC71",
    "metropolitan": "#F39C12",
    "metropolitian": "#F39C12",
    "semi-urban": "#E74C3C",
    "semi urban": "#E74C3C",
}

VEHICLE_TYPE_COLOR_MAP = {
    "motorcycle": "#1F77B4",
    "scooter": "#3498DB",
    "electric_scooter": "#2ECC71",
    "electric scooter": "#2ECC71",
}

ORDER_TYPE_COLOR_MAP = {
    "Meal": "#D35400",
    "Buffet": "#8E44AD",
    "Snack": "#F39C12",
    "Drinks": "#3498DB",
}

CORPORATE_COLORS = {
    "primary_blue": "#2C3E50",
    "secondary_steel": "#34495E",
    "high_perf": "#1E8449",
    "medium_perf": "#D68910",
    "low_perf": "#922B21",
    "distribution_teal": "#117A65",
    "light_neutral": "#85929E",
}


_original_plotly_chart = st.plotly_chart


def get_theme_config():
    return THEME_CONFIGS["light"]


def get_mapbox_style_for_theme():
    return "carto-positron"


def semantic_bucket(label):
    label_text = str(label).strip().lower()
    if any(term in label_text for term in ["sunny", "clear", "low", "optimal", "fast"]):
        return "optimal"
    if any(
        term in label_text for term in ["cloudy", "moderate", "medium", "stable", "normal"]
    ):
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
            fig.layout[axis_name].showgrid = False
            fig.layout[axis_name].zeroline = False

    fig.update_xaxes(tickfont_color=secondary_text, title_font_color=secondary_text)
    fig.update_yaxes(tickfont_color=secondary_text, title_font_color=secondary_text)

    if "mapbox" in fig.layout:
        fig.update_layout(mapbox_style=get_mapbox_style_for_theme())

    chart_title = ""
    if getattr(fig.layout, "title", None) is not None:
        chart_title = str(getattr(fig.layout.title, "text", "") or "").strip()

    if chart_title == "Delivery Time Distribution":
        for trace in fig.data:
            if getattr(trace, "type", None) == "bar" and trace.y is not None:
                y_values = np.array(trace.y, dtype=float)
                if y_values.size > 0 and np.nanmax(y_values) > np.nanmin(y_values):
                    norm = (y_values - np.nanmin(y_values)) / (
                        np.nanmax(y_values) - np.nanmin(y_values)
                    )
                else:
                    norm = np.zeros_like(y_values, dtype=float)

                color_stops = [
                    np.array([220, 38, 38]),
                    np.array([249, 115, 22]),
                    np.array([250, 204, 21]),
                    np.array([125, 211, 252]),
                    np.array([37, 99, 235]),
                ]

                segment_idx = np.clip((norm * 4).astype(int), 0, 3)
                segment_start = segment_idx / 4
                segment_ratio = ((norm - segment_start) * 4)[:, None]
                rgb_values = np.array(
                    [
                        color_stops[idx] + (color_stops[idx + 1] - color_stops[idx]) * ratio
                        for idx, ratio in zip(segment_idx, segment_ratio)
                    ]
                )

                colors = [
                    f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
                    for rgb in rgb_values
                ]
                trace.marker = dict(
                    color=colors,
                    line=dict(width=0.5, color=config["marker_line"]),
                )

    if chart_title == "Avg Distance per City":
        for trace in fig.data:
            if getattr(trace, "type", None) == "bar" and trace.x is not None:
                city_colors = [
                    AVG_DISTANCE_CITY_COLOR_MAP.get(str(city).strip().lower(), "#475569")
                    for city in trace.x
                ]
                trace.marker = dict(
                    color=city_colors,
                    line=dict(width=0.5, color=config["marker_line"]),
                )

    if len(fig.data) == 1 and getattr(fig.data[0], "type", None) == "bar":
        trace = fig.data[0]
        values = trace.x if trace.x is not None else trace.y
        count = len(values) if values is not None else 0
        marker = getattr(trace, "marker", None)
        has_colorscale = marker is not None and getattr(marker, "colorscale", None) is not None
        marker_color = getattr(marker, "color", None) if marker is not None else None
        has_explicit_color_array = (
            marker_color is not None
            and not isinstance(marker_color, str)
            and hasattr(marker_color, "__len__")
            and len(marker_color) == count
        )

        if count > 1 and not has_colorscale and not has_explicit_color_array:
            trace.marker = dict(
                color=[semantic_color_for_label(value, config) for value in values],
                line=dict(width=0.5, color=config["marker_line"]),
            )

    if (
        len(fig.data) == 1
        and getattr(fig.data[0], "type", None) == "histogram"
        and chart_title != "Efficiency Score Distribution"
    ):
        fig.data[0].marker = dict(
            color=config["semantic"]["neutral"],
            line=dict(width=0.5, color=config["marker_line"]),
        )

    if chart_title == "Efficiency Score Distribution" and len(fig.data) == 1:
        fig.data[0].marker = dict(
            color=CORPORATE_COLORS["distribution_teal"],
            line=dict(width=0.5, color=config["marker_line"]),
        )
        fig.data[0].opacity = 0.85

    for trace in fig.data:
        if getattr(trace, "type", None) == "pie" and getattr(trace, "labels", None) is not None:
            pie_marker = getattr(trace, "marker", None)
            existing_colors = getattr(pie_marker, "colors", None) if pie_marker is not None else None
            has_explicit_pie_colors = (
                existing_colors is not None
                and hasattr(existing_colors, "__len__")
                and len(existing_colors) == len(trace.labels)
            )

            if has_explicit_pie_colors:
                trace.marker.line = dict(width=1, color=config["marker_line"])
            else:
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


def themed_plotly_chart(figure_or_data, **kwargs):
    if hasattr(figure_or_data, "update_layout"):
        figure_or_data = apply_compact_chart_theme(figure_or_data)
    return _original_plotly_chart(figure_or_data, **kwargs)


def configure_ui():
    if st.session_state.get("_ui_configured", False):
        return

    st.set_page_config(page_title="Zomato Delivery Intelligence Dashboard", layout="wide")
    st.plotly_chart = themed_plotly_chart
    apply_plotly_defaults_for_theme()
    st.session_state["_ui_configured"] = True


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
        city_color_map = {
            "metropolitan": "#059669",
            "metropolitian": "#059669",
            "urban": "#FACC15",
            "semi-urban": "#DC2626",
            "semi urban": "#DC2626",
        }
        city_colors = [
            city_color_map.get(str(city).strip().lower(), "#475569")
            for city in city_orders["City"]
        ]
        fig.update_traces(marker=dict(color=city_colors))
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
        weather_colors = [
            WEATHER_COLOR_MAP.get(str(weather).strip(), "#475569")
            for weather in weather_orders["Weather_conditions"]
        ]
        fig.update_traces(marker=dict(color=weather_colors))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        valid_times = df["Time_taken (min)"].dropna()
        hist_counts, bin_edges = np.histogram(valid_times, bins=40)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        color_stops = [
            np.array([220, 38, 38]),
            np.array([249, 115, 22]),
            np.array([250, 204, 21]),
            np.array([125, 211, 252]),
            np.array([37, 99, 235]),
        ]
        if hist_counts.max() > hist_counts.min():
            norm = (hist_counts - hist_counts.min()) / (hist_counts.max() - hist_counts.min())
        else:
            norm = np.zeros_like(hist_counts, dtype=float)

        segment_idx = np.clip((norm * 4).astype(int), 0, 3)
        segment_start = segment_idx / 4
        segment_ratio = ((norm - segment_start) * 4)[:, None]
        rgb_values = np.array(
            [
                color_stops[idx] + (color_stops[idx + 1] - color_stops[idx]) * ratio
                for idx, ratio in zip(segment_idx, segment_ratio)
            ]
        )

        bar_colors = [
            f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
            for rgb in rgb_values
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=bin_centers,
                    y=hist_counts,
                    marker=dict(
                        color=bar_colors,
                    ),
                    hovertemplate="Time: %{x:.1f} min<br>Orders: %{y}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            title="Delivery Time Distribution",
            xaxis_title="Time_taken (min)",
            yaxis_title="Count",
            bargap=0.05,
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
        city_time_fig = px.bar(city_time, x="City", y="Time_taken (min)", title="Avg Delivery Time by City")
        city_time_colors = [
            AVG_DELIVERY_CITY_COLOR_MAP.get(str(city).strip().lower(), "#475569")
            for city in city_time["City"]
        ]
        city_time_fig.update_traces(marker=dict(color=city_time_colors))
        st.plotly_chart(
            city_time_fig,
            use_container_width=True,
        )

        weather_time = (
            df.groupby("Weather_conditions", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        weather_time_fig = px.bar(
            weather_time,
            x="Weather_conditions",
            y="Time_taken (min)",
            title="Avg Delivery Time by Weather",
        )
        weather_time_colors = [
            WEATHER_COLOR_MAP.get(str(weather).strip(), "#475569")
            for weather in weather_time["Weather_conditions"]
        ]
        weather_time_fig.update_traces(marker=dict(color=weather_time_colors))
        st.plotly_chart(
            weather_time_fig,
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
        vehicle_time_fig = px.bar(
            vehicle_time,
            x="Type_of_vehicle",
            y="Time_taken (min)",
            title="Avg Delivery Time by Vehicle Type",
        )
        vehicle_time_colors = [
            VEHICLE_TYPE_COLOR_MAP.get(str(vehicle).strip().lower(), "#475569")
            for vehicle in vehicle_time["Type_of_vehicle"]
        ]
        vehicle_time_fig.update_traces(marker=dict(color=vehicle_time_colors))
        st.plotly_chart(
            vehicle_time_fig,
            use_container_width=True,
        )

        order_type_time = (
            df.groupby("Type_of_order", as_index=False)["Time_taken (min)"]
            .mean()
            .sort_values("Time_taken (min)", ascending=False)
        )
        order_type_time_fig = px.bar(
            order_type_time,
            x="Type_of_order",
            y="Time_taken (min)",
            title="Avg Delivery Time by Type of Order",
        )
        order_type_colors = [
            ORDER_TYPE_COLOR_MAP.get(str(order_type).strip(), "#475569")
            for order_type in order_type_time["Type_of_order"]
        ]
        order_type_time_fig.update_traces(marker=dict(color=order_type_colors))
        st.plotly_chart(
            order_type_time_fig,
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
        avg_dist_city_fig = px.bar(avg_dist_city, x="City", y="distance_km", title="Avg Distance per City")
        avg_dist_city_colors = [
            AVG_DISTANCE_CITY_COLOR_MAP.get(str(city).strip().lower(), "#475569")
            for city in avg_dist_city["City"]
        ]
        avg_dist_city_fig.update_traces(marker=dict(color=avg_dist_city_colors))
        st.plotly_chart(
            avg_dist_city_fig,
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
        distance_category_pie.update_traces(
            marker=dict(
                colors=[
                    DISTANCE_CATEGORY_COLOR_MAP.get(str(label).strip(), "#475569")
                    for label in dist_cat["distance_category"]
                ]
            )
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
        top10 = rider_grp.nlargest(10, "efficiency_score").sort_values("efficiency_score", ascending=False)
        top10_fig = px.bar(
            top10,
            x="efficiency_score",
            y="Delivery_person_ID",
            orientation="h",
            title="Top 10 Riders by Efficiency",
        )
        top10_fig.update_traces(
            marker=dict(
                color=[CORPORATE_COLORS["high_perf"]] * len(top10),
            )
        )
        top10_fig.update_yaxes(
            categoryorder="array",
            categoryarray=top10["Delivery_person_ID"].tolist(),
            autorange="reversed",
        )
        st.plotly_chart(top10_fig, use_container_width=True)

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
        order_values = orders_by_rider["orders"].to_numpy(dtype=float)
        if order_values.max() > order_values.min():
            order_norm = (order_values - order_values.min()) / (order_values.max() - order_values.min())
        else:
            order_norm = np.zeros_like(order_values, dtype=float)

        low_rgb = np.array([133, 146, 158])
        high_rgb = np.array([44, 62, 80])
        order_rgb = low_rgb + (high_rgb - low_rgb) * order_norm[:, None]
        order_colors = [
            f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
            for rgb in order_rgb
        ]

        orders_by_rider_fig = px.bar(
            orders_by_rider,
            x="Delivery_person_ID",
            y="orders",
            title="Orders Completed by Rider (Top 30)",
        )
        orders_by_rider_fig.update_traces(marker=dict(color=order_colors))
        st.plotly_chart(orders_by_rider_fig, use_container_width=True)

    with col2:
        bottom10 = rider_grp.nsmallest(10, "efficiency_score").sort_values("efficiency_score")
        bottom10_fig = px.bar(
            bottom10,
            x="efficiency_score",
            y="Delivery_person_ID",
            orientation="h",
            title="Bottom 10 Riders",
        )
        bottom10_fig.update_traces(
            marker=dict(
                color=[CORPORATE_COLORS["low_perf"]] * len(bottom10),
            )
        )
        bottom10_fig.update_yaxes(
            categoryorder="array",
            categoryarray=bottom10["Delivery_person_ID"].tolist(),
            autorange="reversed",
        )
        st.plotly_chart(bottom10_fig, use_container_width=True)

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

        efficiency_dist_fig = px.histogram(
            rider_grp,
            x="efficiency_score",
            nbins=30,
            title="Efficiency Score Distribution",
        )
        efficiency_dist_fig.update_traces(
            marker=dict(color=CORPORATE_COLORS["distribution_teal"]),
            opacity=0.85,
        )
        efficiency_dist_fig.update_xaxes(showgrid=False)
        efficiency_dist_fig.update_yaxes(showgrid=False)
        st.plotly_chart(efficiency_dist_fig, use_container_width=True)

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
        max_month_orders = monthly["orders"].max() if not monthly.empty else None
        monthly_colors = [
            CORPORATE_COLORS["high_perf"]
            if max_month_orders is not None and orders == max_month_orders
            else CORPORATE_COLORS["secondary_steel"]
            for orders in monthly["orders"]
        ]
        monthly_fig = px.bar(monthly, x="order_month", y="orders", title="Orders per Month")
        monthly_fig.update_traces(marker=dict(color=monthly_colors))
        st.plotly_chart(
            monthly_fig,
            use_container_width=True,
        )

        hour_df = (
            df.dropna(subset=["order_hour"])
            .groupby("order_hour", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
            .sort_values("order_hour")
        )
        hour_values = hour_df["orders"].to_numpy(dtype=float)
        if hour_values.size > 0 and hour_values.max() > hour_values.min():
            hour_norm = (hour_values - hour_values.min()) / (hour_values.max() - hour_values.min())
        else:
            hour_norm = np.zeros_like(hour_values, dtype=float)
        low_rgb = np.array([133, 146, 158])
        high_rgb = np.array([44, 62, 80])
        hour_rgb = low_rgb + (high_rgb - low_rgb) * hour_norm[:, None]
        hour_colors = [
            f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
            for rgb in hour_rgb
        ]
        orders_per_hour_fig = px.bar(hour_df, x="order_hour", y="orders", title="Orders per Hour")
        orders_per_hour_fig.update_traces(marker=dict(color=hour_colors))
        st.plotly_chart(
            orders_per_hour_fig,
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
        peak_values = peak_hours["orders"].to_numpy(dtype=float)
        if peak_values.size > 0 and peak_values.max() > peak_values.min():
            peak_norm = (peak_values - peak_values.min()) / (peak_values.max() - peak_values.min())
        else:
            peak_norm = np.zeros_like(peak_values, dtype=float)
        peak_low_rgb = np.array([213, 245, 227])
        peak_high_rgb = np.array([30, 132, 73])
        peak_rgb = peak_low_rgb + (peak_high_rgb - peak_low_rgb) * peak_norm[:, None]
        peak_colors = [
            f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
            for rgb in peak_rgb
        ]
        peak_hours_fig = px.bar(peak_hours, x="order_hour", y="orders", title="Peak Order Hours (Top 5)")
        peak_hours_fig.update_traces(marker=dict(color=peak_colors))
        st.plotly_chart(
            peak_hours_fig,
            use_container_width=True,
        )

        festival_cmp = (
            df.groupby("Festival", as_index=False)
            .size()
            .rename(columns={"size": "orders"})
        )
        festival_cmp_colors = [
            CORPORATE_COLORS["medium_perf"]
            if str(value).strip().lower() == "yes"
            else CORPORATE_COLORS["primary_blue"]
            for value in festival_cmp["Festival"]
        ]
        festival_cmp_fig = px.bar(
            festival_cmp,
            x="Festival",
            y="orders",
            title="Festival vs Normal Day Order Comparison",
        )
        festival_cmp_fig.update_traces(marker=dict(color=festival_cmp_colors))
        st.plotly_chart(
            festival_cmp_fig,
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
        weather_vs_time_fig = px.bar(
            weather_vs_time,
            x="Weather_conditions",
            y="Time_taken (min)",
            title="Weather vs Delivery Time",
        )
        weather_vs_time_colors = [
            WEATHER_COLOR_MAP.get(str(weather).strip(), "#475569")
            for weather in weather_vs_time["Weather_conditions"]
        ]
        weather_vs_time_fig.update_traces(marker=dict(color=weather_vs_time_colors))
        st.plotly_chart(
            weather_vs_time_fig,
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
        festival_impact_colors = [
            "#2ECC71"
            if str(value).strip().lower() == "yes"
            else "#E74C3C"
            for value in festival_impact["Festival"]
        ]
        festival_impact_fig = px.bar(
            festival_impact,
            x="Festival",
            y="Time_taken (min)",
            title="Festival Impact on Delivery Time",
        )
        festival_impact_fig.update_traces(marker=dict(color=festival_impact_colors))
        st.plotly_chart(
            festival_impact_fig,
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


def predictive_analytics_page(df, train_predictive_models):
    st.subheader("Predictive Analytics")

    with st.spinner("Training regression and delay classification models..."):
        model_bundle = train_predictive_models(df)

    metric_card_row(
        {
            "Regression R2": f"{model_bundle['r2']:.4f}",
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
        reg_top = model_bundle["reg_importances"].head(15).copy()
        reg_fig = px.bar(
            reg_top,
            x="importance",
            y="feature",
            orientation="h",
            title="Feature Importance (Regression)",
        )
        reg_colors = [CORPORATE_COLORS["primary_blue"]] * len(reg_top)
        for idx in range(min(3, len(reg_colors))):
            reg_colors[idx] = CORPORATE_COLORS["distribution_teal"]
        reg_fig.update_traces(marker=dict(color=reg_colors))
        st.plotly_chart(
            reg_fig,
            use_container_width=True,
        )

    with col5:
        cls_top = model_bundle["cls_importances"].head(15).copy()
        cls_values = cls_top["importance"].to_numpy(dtype=float)
        if cls_values.size > 0 and cls_values.max() > cls_values.min():
            cls_norm = (cls_values - cls_values.min()) / (cls_values.max() - cls_values.min())
        else:
            cls_norm = np.zeros_like(cls_values, dtype=float)

        risk_stops = [
            np.array([133, 146, 158]),
            np.array([214, 137, 16]),
            np.array([146, 43, 33]),
        ]
        cls_segment_idx = np.clip((cls_norm * 2).astype(int), 0, 1)
        cls_segment_start = cls_segment_idx / 2
        cls_segment_ratio = ((cls_norm - cls_segment_start) * 2)[:, None]
        cls_rgb = np.array(
            [
                risk_stops[idx] + (risk_stops[idx + 1] - risk_stops[idx]) * ratio
                for idx, ratio in zip(cls_segment_idx, cls_segment_ratio)
            ]
        )
        cls_colors = [
            f"rgb({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
            for rgb in cls_rgb
        ]

        cls_fig = px.bar(
            cls_top,
            x="importance",
            y="feature",
            orientation="h",
            title="Feature Importance (Delay Classification)",
        )
        cls_fig.update_traces(marker=dict(color=cls_colors))
        st.plotly_chart(
            cls_fig,
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

        del_points = base_map_df[
            ["Delivery_location_latitude", "Delivery_location_longitude"]
        ].rename(columns={"Delivery_location_latitude": "lat", "Delivery_location_longitude": "lon"})
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
    st.sidebar.markdown("### Filters")
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

    with st.sidebar.expander("On-Time Threshold", expanded=False):
        selected_threshold = st.slider(
            "On-Time Threshold (min)",
            min_value=20,
            max_value=45,
            key="on_time_threshold",
        )

    if selected_threshold != current_threshold:
        st.rerun()

    with st.sidebar.expander("Geography", expanded=True):
        st.multiselect(
            "City",
            city_options,
            key="selected_cities",
            placeholder="Choose one or more cities",
        )

    with st.sidebar.expander("Operating Conditions", expanded=True):
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

    with st.sidebar.expander("Delivery Time", expanded=False):
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
