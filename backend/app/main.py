from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .core import (
    demand_time_payload,
    delivery_operations_payload,
    external_impact_payload,
    executive_overview_payload,
    filter_dataframe,
    load_and_prepare_data,
    location_intelligence_payload,
    predictive_assets_payload,
    rider_efficiency_payload,
    train_predictive_models,
)
from .schemas import FiltersRequest, PredictionRequest

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "Zomato Dataset.csv"

app = FastAPI(title="Zomato Delivery API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_dataset(on_time_threshold: int):
    df, missing = load_and_prepare_data(DATA_PATH, on_time_threshold)
    if df is None:
        raise HTTPException(status_code=500, detail={"missing_columns": missing})
    return df


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/filters/options")
def filter_options(on_time_threshold: int = 30):
    df = _load_dataset(on_time_threshold)
    time_min = int(df["Time_taken (min)"].dropna().min())
    time_max = int(df["Time_taken (min)"].dropna().max())
    return {
        "cities": sorted(df["City"].dropna().unique().tolist()),
        "weather": sorted(df["Weather_conditions"].dropna().unique().tolist()),
        "traffic": sorted(df["Road_traffic_density"].dropna().unique().tolist()),
        "time_min": time_min,
        "time_max": time_max,
        "default_on_time_threshold": 30,
    }


@app.post("/api/filters/apply")
def apply_filters(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return {
        "matching_orders": int(len(filtered)),
        "total_orders": int(len(df)),
    }


@app.post("/api/executive-overview")
def executive_overview(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    if filtered.empty:
        return {"metrics": {}, "trend": [], "city_orders": []}
    return executive_overview_payload(filtered, req.on_time_threshold)


@app.post("/api/delivery-operations")
def delivery_operations(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return delivery_operations_payload(filtered)


@app.post("/api/rider-efficiency")
def rider_efficiency(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return rider_efficiency_payload(filtered, req.on_time_threshold)


@app.post("/api/demand-time")
def demand_time(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return demand_time_payload(filtered)


@app.post("/api/external-impact")
def external_impact(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return external_impact_payload(filtered, req.on_time_threshold)


@app.post("/api/location-intelligence")
def location_intelligence(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return location_intelligence_payload(filtered)


@app.post("/api/predictive-assets")
def predictive_assets(req: FiltersRequest):
    df = _load_dataset(req.on_time_threshold)
    filtered = filter_dataframe(df, req.cities, req.weather, req.traffic, req.time_min, req.time_max)
    return predictive_assets_payload(filtered)


@app.post("/api/predict")
def predict(req: PredictionRequest):
    df = _load_dataset(30)
    models = train_predictive_models(df)

    row = pd.DataFrame(
        [
            {
                "Weather_conditions": req.weather_conditions,
                "Road_traffic_density": req.road_traffic_density,
                "City": req.city,
                "Festival": req.festival,
                "Vehicle_condition": req.vehicle_condition,
                "Type_of_order": req.type_of_order,
                "Type_of_vehicle": req.type_of_vehicle,
                "multiple_deliveries": req.multiple_deliveries,
                "Delivery_person_Ratings": req.delivery_person_ratings,
                "Delivery_person_Age": req.delivery_person_age,
                "distance_km": req.distance_km,
            }
        ]
    )

    pred_time = float(models["reg_pipeline"].predict(row)[0])
    delay_prob = float(models["cls_pipeline"].predict_proba(row)[0][1] * 100)

    return {
        "predicted_delivery_time": pred_time,
        "delay_probability": delay_prob,
        "r2": models["r2"],
        "mae": models["mae"],
        "confusion_matrix": models["confusion_matrix"],
    }
