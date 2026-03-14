export type FiltersRequest = {
  on_time_threshold: number;
  cities: string[] | null;
  weather: string[] | null;
  traffic: string[] | null;
  time_min: number | null;
  time_max: number | null;
};

export type PageName =
  | "Executive Overview"
  | "Delivery Operations"
  | "Rider Efficiency"
  | "Demand & Time Analysis"
  | "External Impact Analysis"
  | "Predictive Analytics"
  | "Location Intelligence";

export type FilterOptions = {
  cities: string[];
  weather: string[];
  traffic: string[];
  time_min: number;
  time_max: number;
  default_on_time_threshold: number;
};

export type ExecutiveOverviewResponse = {
  metrics: {
    total_orders: number;
    avg_delivery_time: number;
    on_time_pct: number;
    avg_rating: number;
    avg_age: number;
    active_riders: number;
    festival_orders_pct: number;
    non_festival_orders_pct: number;
    on_time_threshold: number;
  };
  trend: Array<{ order_date: string; orders: number }>;
  city_orders: Array<{ city: string; orders: number }>;
};

export type DeliveryOperationsResponse = {
  city_time: Array<Record<string, string | number>>;
  weather_time: Array<Record<string, string | number>>;
  traffic_time: Array<Record<string, string | number>>;
  vehicle_time: Array<Record<string, string | number>>;
  order_type_time: Array<Record<string, string | number>>;
  distance_scatter: Array<Record<string, string | number>>;
  avg_dist_city: Array<Record<string, string | number>>;
  distance_category: Array<Record<string, string | number>>;
};

export type RiderEfficiencyResponse = {
  metrics: Record<string, number>;
  top10: Array<Record<string, string | number>>;
  bottom10: Array<Record<string, string | number>>;
  orders_by_rider: Array<Record<string, string | number>>;
  rating_vs_time: Array<Record<string, string | number>>;
  age_vs_perf: Array<Record<string, string | number>>;
  efficiency_hist: { bins: number[]; counts: number[] };
  ranking: Array<Record<string, string | number>>;
};

export type DemandTimeResponse = {
  daily: Array<Record<string, string | number>>;
  monthly: Array<Record<string, string | number>>;
  hourly: Array<Record<string, string | number>>;
  peak_hours: Array<Record<string, string | number>>;
  festival_cmp: Array<Record<string, string | number>>;
  city_trend: Array<Record<string, string | number>>;
};

export type ExternalImpactResponse = {
  on_time_threshold: number;
  weather_vs_time: Array<Record<string, string | number>>;
  traffic_vs_time: Array<Record<string, string | number>>;
  festival_impact: Array<Record<string, string | number>>;
  vehicle_condition_perf: Array<Record<string, string | number>>;
};

export type LocationIntelligenceResponse = {
  density: Array<Record<string, string | number>>;
  delay_zones: Array<Record<string, string | number>>;
  avg_map: Array<Record<string, string | number>>;
  distribution_points: Array<Record<string, string | number>>;
};

export type PredictiveAssetsResponse = {
  r2: number;
  mae: number;
  confusion_matrix: number[][];
  reg_importances: Array<Record<string, string | number>>;
  cls_importances: Array<Record<string, string | number>>;
  options: {
    weather_conditions: string[];
    road_traffic_density: string[];
    city: string[];
    festival: string[];
    type_of_order: string[];
    type_of_vehicle: string[];
  };
};

export type PredictionResponse = {
  predicted_delivery_time: number;
  delay_probability: number;
  r2: number;
  mae: number;
  confusion_matrix: number[][];
};
