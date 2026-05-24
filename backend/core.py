from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

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
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return radius * c


def load_and_prepare_data(file_path: str | Path, on_time_threshold: int = 30):
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

    df["Order_Date"] = pd.to_datetime(df["Order_Date"], format="%d-%m-%y", errors="coerce")

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


def train_predictive_models(df: pd.DataFrame):
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

    model_df = df[feature_cols + ["Time_taken (min)", "is_delayed"]].copy()
    model_df = model_df.dropna(subset=["Time_taken (min)"])

    x = model_df[feature_cols]
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
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_cols,
            ),
            ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]), numeric_cols),
        ]
    )

    x_train, x_test, y_reg_train, y_reg_test = train_test_split(x, y_reg, test_size=0.2, random_state=42)
    _, _, y_cls_train, y_cls_test = train_test_split(x, y_cls, test_size=0.2, random_state=42)

    reg_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1, max_depth=14)),
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

    reg_pipeline.fit(x_train, y_reg_train)
    cls_pipeline.fit(x_train, y_cls_train)

    reg_pred = reg_pipeline.predict(x_test)
    cls_pred = cls_pipeline.predict(x_test)

    r2 = r2_score(y_reg_test, reg_pred)
    mae = mean_absolute_error(y_reg_test, reg_pred)
    cm = confusion_matrix(y_cls_test, cls_pred)

    return {
        "reg_pipeline": reg_pipeline,
        "cls_pipeline": cls_pipeline,
        "r2": float(r2),
        "mae": float(mae),
        "confusion_matrix": cm.tolist(),
    }


def filter_dataframe(
    df: pd.DataFrame,
    cities: list[str] | None,
    weather: list[str] | None,
    traffic: list[str] | None,
    time_min: int | None,
    time_max: int | None,
):
    selected_cities = cities if cities else sorted(df["City"].dropna().unique().tolist())
    selected_weather = weather if weather else sorted(df["Weather_conditions"].dropna().unique().tolist())
    selected_traffic = traffic if traffic else sorted(df["Road_traffic_density"].dropna().unique().tolist())

    low = int(time_min) if time_min is not None else int(np.floor(df["Time_taken (min)"].dropna().min()))
    high = int(time_max) if time_max is not None else int(np.ceil(df["Time_taken (min)"].dropna().max()))

    out = df[
        df["City"].isin(selected_cities)
        & df["Weather_conditions"].isin(selected_weather)
        & df["Road_traffic_density"].isin(selected_traffic)
        & df["Time_taken (min)"].between(low, high)
    ].copy()
    return out


def executive_overview_payload(df: pd.DataFrame, on_time_threshold: int):
    total_orders = len(df)
    avg_delivery_time = float(df["Time_taken (min)"].mean())
    on_time_pct = float(df["is_on_time"].mean() * 100)
    avg_rating = float(df["Delivery_person_Ratings"].mean())
    avg_age = float(df["Delivery_person_Age"].mean())
    active_riders = int(df["Delivery_person_ID"].nunique())
    festival_orders_pct = float(df["Festival"].eq("Yes").mean() * 100)

    trend = (
        df.dropna(subset=["Order_Date"])
        .groupby("Order_Date", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )

    city_orders = (
        df.groupby("City", dropna=False, as_index=False)
        .size()
        .rename(columns={"size": "orders"})
        .sort_values("orders", ascending=False)
    )

    return {
        "metrics": {
            "total_orders": total_orders,
            "avg_delivery_time": avg_delivery_time,
            "on_time_pct": on_time_pct,
            "avg_rating": avg_rating,
            "avg_age": avg_age,
            "active_riders": active_riders,
            "festival_orders_pct": festival_orders_pct,
            "non_festival_orders_pct": float(100 - festival_orders_pct),
            "on_time_threshold": on_time_threshold,
        },
        "trend": [
            {"order_date": d.strftime("%Y-%m-%d"), "orders": int(o)}
            for d, o in zip(trend["Order_Date"], trend["orders"])
        ],
        "city_orders": [
            {"city": str(c), "orders": int(o)}
            for c, o in zip(city_orders["City"], city_orders["orders"])
        ],
    }


def sampled_df(df: pd.DataFrame, n: int = 5000):
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=42)


def _records(frame: pd.DataFrame):
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
    return out.to_dict(orient="records")


def delivery_operations_payload(df: pd.DataFrame):
    city_time = (
        df.groupby("City", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    weather_time = (
        df.groupby("Weather_conditions", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    traffic_time = (
        df.groupby("Road_traffic_density", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    vehicle_time = (
        df.groupby("Type_of_vehicle", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    order_type_time = (
        df.groupby("Type_of_order", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    scatter_df = sampled_df(df.dropna(subset=["distance_km", "Time_taken (min)"]), n=8000)
    avg_dist_city = (
        df.groupby("City", as_index=False)["distance_km"]
        .mean()
        .sort_values("distance_km", ascending=False)
    )
    dist_cat = (
        df.groupby("distance_category", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )

    return {
        "city_time": _records(city_time),
        "weather_time": _records(weather_time),
        "traffic_time": _records(traffic_time),
        "vehicle_time": _records(vehicle_time),
        "order_type_time": _records(order_type_time),
        "distance_scatter": _records(
            scatter_df[["distance_km", "Time_taken (min)", "Road_traffic_density"]]
        ),
        "avg_dist_city": _records(avg_dist_city),
        "distance_category": _records(dist_cat),
    }


def rider_efficiency_payload(df: pd.DataFrame, on_time_threshold: int):
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
        100 * (0.35 * rating_norm + 0.30 * time_inv_norm + 0.25 * ontime_norm + 0.10 * multi_inv_norm)
    )

    top10 = rider_grp.nlargest(10, "efficiency_score").sort_values("efficiency_score", ascending=False)
    bottom10 = rider_grp.nsmallest(10, "efficiency_score").sort_values("efficiency_score")
    orders_by_rider = rider_grp.sort_values("orders", ascending=False).head(30)

    hist_counts, bin_edges = np.histogram(rider_grp["efficiency_score"].dropna(), bins=30)

    return {
        "metrics": {
            "total_riders": int(rider_grp["Delivery_person_ID"].nunique()),
            "avg_orders_per_rider": float(rider_grp["orders"].mean()),
            "avg_delivery_time_per_rider": float(rider_grp["avg_delivery_time"].mean()),
            "avg_on_time_pct": float(rider_grp["on_time_pct"].mean()),
            "avg_rating_per_rider": float(rider_grp["avg_rating"].mean()),
            "avg_multiple_deliveries": float(rider_grp["avg_multiple_deliveries"].mean()),
            "on_time_threshold": on_time_threshold,
        },
        "top10": _records(top10),
        "bottom10": _records(bottom10),
        "orders_by_rider": _records(orders_by_rider),
        "rating_vs_time": _records(
            rider_grp[["avg_rating", "avg_delivery_time", "orders", "Delivery_person_ID", "efficiency_score"]]
        ),
        "age_vs_perf": _records(
            rider_grp[["avg_age", "avg_delivery_time", "efficiency_score", "Delivery_person_ID", "orders"]]
        ),
        "efficiency_hist": {
            "bins": ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist(),
            "counts": hist_counts.tolist(),
        },
        "ranking": _records(
            rider_grp.sort_values("efficiency_score", ascending=False).reset_index(drop=True).head(300)
        ),
    }


def demand_time_payload(df: pd.DataFrame):
    daily = (
        df.dropna(subset=["Order_Date"])
        .groupby("Order_Date", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )
    monthly = (
        df.dropna(subset=["order_month"])
        .groupby("order_month", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )
    hour_df = (
        df.dropna(subset=["order_hour"])
        .groupby("order_hour", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
        .sort_values("order_hour")
    )
    peak_hours = hour_df.sort_values("orders", ascending=False).head(5)
    festival_cmp = (
        df.groupby("Festival", as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )
    city_trend = (
        df.dropna(subset=["Order_Date", "City"])
        .groupby(["Order_Date", "City"], as_index=False)
        .size()
        .rename(columns={"size": "orders"})
    )

    return {
        "daily": _records(daily),
        "monthly": _records(monthly),
        "hourly": _records(hour_df),
        "peak_hours": _records(peak_hours),
        "festival_cmp": _records(festival_cmp),
        "city_trend": _records(city_trend),
    }


def external_impact_payload(df: pd.DataFrame, on_time_threshold: int):
    weather_vs_time = (
        df.groupby("Weather_conditions", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    traffic_vs_time = (
        df.groupby("Road_traffic_density", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    festival_impact = (
        df.groupby("Festival", as_index=False)["Time_taken (min)"]
        .mean()
        .sort_values("Time_taken (min)", ascending=False)
    )
    vehicle_condition_perf = (
        df.groupby("Vehicle_condition", as_index=False)
        .agg(avg_delivery_time=("Time_taken (min)", "mean"), on_time_pct=("is_on_time", "mean"))
        .sort_values("Vehicle_condition")
    )
    vehicle_condition_perf["on_time_pct"] = vehicle_condition_perf["on_time_pct"] * 100

    return {
        "on_time_threshold": on_time_threshold,
        "weather_vs_time": _records(weather_vs_time),
        "traffic_vs_time": _records(traffic_vs_time),
        "festival_impact": _records(festival_impact),
        "vehicle_condition_perf": _records(vehicle_condition_perf),
    }


def location_intelligence_payload(df: pd.DataFrame):
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

    delay_zones = base_map_df[base_map_df["is_delayed"] == 1]
    grid_df = base_map_df.copy()
    grid_df["grid_lat"] = grid_df["Restaurant_latitude"].round(2)
    grid_df["grid_lon"] = grid_df["Restaurant_longitude"].round(2)
    avg_map = (
        grid_df.groupby(["grid_lat", "grid_lon"], as_index=False)
        .agg(avg_time=("Time_taken (min)", "mean"), orders=("ID", "count"))
        .sort_values("orders", ascending=False)
    )

    rest_points = base_map_df[["Restaurant_latitude", "Restaurant_longitude"]].rename(
        columns={"Restaurant_latitude": "lat", "Restaurant_longitude": "lon"}
    )
    rest_points["point_type"] = "Restaurant"
    del_points = base_map_df[["Delivery_location_latitude", "Delivery_location_longitude"]].rename(
        columns={"Delivery_location_latitude": "lat", "Delivery_location_longitude": "lon"}
    )
    del_points["point_type"] = "Delivery"
    dist_points = pd.concat([rest_points, del_points], ignore_index=True)

    return {
        "density": _records(
            base_map_df[
                ["Restaurant_latitude", "Restaurant_longitude", "City", "Time_taken (min)", "is_delayed"]
            ]
        ),
        "delay_zones": _records(
            delay_zones[["Delivery_location_latitude", "Delivery_location_longitude", "Time_taken (min)"]]
        ),
        "avg_map": _records(avg_map),
        "distribution_points": _records(dist_points),
    }


def predictive_assets_payload(df: pd.DataFrame):
    model_bundle = train_predictive_models(df)

    options = {
        "weather_conditions": sorted(df["Weather_conditions"].dropna().unique().tolist()),
        "road_traffic_density": sorted(df["Road_traffic_density"].dropna().unique().tolist()),
        "city": sorted(df["City"].dropna().unique().tolist()),
        "festival": sorted(df["Festival"].dropna().unique().tolist()),
        "type_of_order": sorted(df["Type_of_order"].dropna().unique().tolist()),
        "type_of_vehicle": sorted(df["Type_of_vehicle"].dropna().unique().tolist()),
    }

    reg_preprocessor = model_bundle["reg_pipeline"].named_steps["preprocessor"]
    reg_model = model_bundle["reg_pipeline"].named_steps["model"]
    reg_importances = pd.DataFrame(
        {"feature": reg_preprocessor.get_feature_names_out(), "importance": reg_model.feature_importances_}
    ).sort_values("importance", ascending=False)

    cls_preprocessor = model_bundle["cls_pipeline"].named_steps["preprocessor"]
    cls_model = model_bundle["cls_pipeline"].named_steps["model"]
    cls_importances = pd.DataFrame(
        {"feature": cls_preprocessor.get_feature_names_out(), "importance": cls_model.feature_importances_}
    ).sort_values("importance", ascending=False)

    return {
        "r2": model_bundle["r2"],
        "mae": model_bundle["mae"],
        "confusion_matrix": model_bundle["confusion_matrix"],
        "reg_importances": _records(reg_importances.head(20)),
        "cls_importances": _records(cls_importances.head(20)),
        "options": options,
    }