import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ui import (
    apply_app_theme,
    configure_ui,
    delivery_operations_page,
    demand_time_analysis_page,
    executive_overview_page,
    external_impact_page,
    location_intelligence_page,
    predictive_analytics_page,
    render_sidebar_filters,
    rider_efficiency_page,
)

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
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_cols,
            ),
            ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]), numeric_cols),
        ]
    )

    X_train, X_test, y_reg_train, y_reg_test = train_test_split(X, y_reg, test_size=0.2, random_state=42)
    _, _, y_cls_train, y_cls_test = train_test_split(X, y_cls, test_size=0.2, random_state=42)

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


def main():
    configure_ui()

    st.sidebar.header("Dashboard Controls")
    data_path = st.sidebar.text_input("Dataset path", "Zomato Dataset.csv")
    on_time_threshold = st.session_state.get("on_time_threshold", 30)

    apply_app_theme()

    st.title("Zomato Delivery Intelligence Dashboard")
    st.caption("Active theme: Light")

    df, missing_columns = load_and_prepare_data(data_path, on_time_threshold)
    if df is None:
        st.error("Missing required columns: " + ", ".join(missing_columns))
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
        predictive_analytics_page(filtered_df, train_predictive_models)
    elif page == "Location Intelligence":
        location_intelligence_page(filtered_df)


if __name__ == "__main__":
    main()
