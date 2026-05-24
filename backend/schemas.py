from __future__ import annotations

from pydantic import BaseModel, Field


class FiltersRequest(BaseModel):
    on_time_threshold: int = Field(default=30, ge=20, le=45)
    cities: list[str] | None = None
    weather: list[str] | None = None
    traffic: list[str] | None = None
    time_min: int | None = None
    time_max: int | None = None


class PredictionRequest(BaseModel):
    weather_conditions: str
    road_traffic_density: str
    city: str
    festival: str
    vehicle_condition: int
    type_of_order: str
    type_of_vehicle: str
    multiple_deliveries: int
    delivery_person_ratings: float
    delivery_person_age: int
    distance_km: float