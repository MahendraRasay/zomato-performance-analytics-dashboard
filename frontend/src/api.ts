import type {
  DemandTimeResponse,
  DeliveryOperationsResponse,
  ExecutiveOverviewResponse,
  ExternalImpactResponse,
  FilterOptions,
  FiltersRequest,
  LocationIntelligenceResponse,
  PredictiveAssetsResponse,
  PredictionResponse,
  RiderEfficiencyResponse,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "http://127.0.0.1:8000";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getFilterOptions(onTimeThreshold: number): Promise<FilterOptions> {
  const res = await fetch(`${API_BASE}/api/filters/options?on_time_threshold=${onTimeThreshold}`);
  return parseJson<FilterOptions>(res);
}

export async function getExecutiveOverview(filters: FiltersRequest): Promise<ExecutiveOverviewResponse> {
  const res = await fetch(`${API_BASE}/api/executive-overview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  });
  return parseJson<ExecutiveOverviewResponse>(res);
}

async function postFilters<T>(endpoint: string, filters: FiltersRequest): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  });
  return parseJson<T>(res);
}

export function getDeliveryOperations(filters: FiltersRequest) {
  return postFilters<DeliveryOperationsResponse>("/api/delivery-operations", filters);
}

export function getRiderEfficiency(filters: FiltersRequest) {
  return postFilters<RiderEfficiencyResponse>("/api/rider-efficiency", filters);
}

export function getDemandTime(filters: FiltersRequest) {
  return postFilters<DemandTimeResponse>("/api/demand-time", filters);
}

export function getExternalImpact(filters: FiltersRequest) {
  return postFilters<ExternalImpactResponse>("/api/external-impact", filters);
}

export function getLocationIntelligence(filters: FiltersRequest) {
  return postFilters<LocationIntelligenceResponse>("/api/location-intelligence", filters);
}

export function getPredictiveAssets(filters: FiltersRequest) {
  return postFilters<PredictiveAssetsResponse>("/api/predictive-assets", filters);
}

export async function predictDelivery(payload: Record<string, string | number>): Promise<PredictionResponse> {
  const res = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<PredictionResponse>(res);
}
