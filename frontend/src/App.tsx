import { useEffect, useMemo, useRef, useState, type ComponentProps } from "react";
import BasePlot from "react-plotly.js";
import {
  getDemandTime,
  getDeliveryOperations,
  getExecutiveOverview,
  getExternalImpact,
  getFilterOptions,
  getLocationIntelligence,
  getPredictiveAssets,
  getRiderEfficiency,
  predictDelivery,
} from "./api";
import type {
  DemandTimeResponse,
  DeliveryOperationsResponse,
  ExecutiveOverviewResponse,
  ExternalImpactResponse,
  FilterOptions,
  FiltersRequest,
  LocationIntelligenceResponse,
  PageName,
  PredictiveAssetsResponse,
  RiderEfficiencyResponse,
} from "./types";

const PAGES: PageName[] = [
  "Executive Overview",
  "Delivery Operations",
  "Rider Efficiency",
  "Demand & Time Analysis",
  "External Impact Analysis",
  "Predictive Analytics",
  "Location Intelligence",
];

const CORPORATE_COLORWAY = ["#1e3a8a", "#2563eb", "#60a5fa", "#10b981", "#f59e0b", "#ef4444"];

const CHART_LAYOUT_BASE: Record<string, unknown> = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "#ffffff",
  font: { color: "#0f172a" },
  colorway: CORPORATE_COLORWAY,
  hoverlabel: { bgcolor: "#ffffff", bordercolor: "#e2e8f0", font: { color: "#0f172a" } },
};

const CHART_CONFIG_BASE = {
  responsive: true,
  displayModeBar: false,
};

function mergeAxisTheme(axis: Record<string, unknown> = {}) {
  return {
    gridcolor: "#e2e8f0",
    zerolinecolor: "#e2e8f0",
    linecolor: "#cbd5e1",
    tickfont: { color: "#475569" },
    ...axis,
  };
}

type PlotProps = ComponentProps<typeof BasePlot>;

function withSemanticTraceColors(data: PlotProps["data"]) {
  if (!Array.isArray(data)) {
    return data;
  }

  return data.map((trace, idx) => {
    const source = trace as Record<string, unknown>;
    const type = String(source.type ?? "").toLowerCase();
    const tone = CORPORATE_COLORWAY[idx % CORPORATE_COLORWAY.length];

    if (type === "scattermap" || type === "scattermapbox" || type === "heatmap") {
      return trace;
    }

    if (type === "bar") {
      const marker = (source.marker as Record<string, unknown>) ?? {};
      if (!("color" in marker)) {
        return { ...source, marker: { ...marker, color: tone } };
      }
      return trace;
    }

    if (type === "pie") {
      const marker = (source.marker as Record<string, unknown>) ?? {};
      if (!("colors" in marker)) {
        const labels = Array.isArray(source.labels) ? source.labels.length : CORPORATE_COLORWAY.length;
        const colors = Array.from({ length: Math.max(labels, 1) }, (_, i) => CORPORATE_COLORWAY[i % CORPORATE_COLORWAY.length]);
        return { ...source, marker: { ...marker, colors } };
      }
      return trace;
    }

    if (type === "scatter") {
      const mode = String(source.mode ?? "lines").toLowerCase();
      const next: Record<string, unknown> = { ...source };

      if (mode.includes("lines")) {
        const line = (source.line as Record<string, unknown>) ?? {};
        if (!("color" in line)) {
          next.line = { ...line, color: tone };
        }
      }

      if (mode.includes("markers")) {
        const marker = (source.marker as Record<string, unknown>) ?? {};
        if (!("color" in marker)) {
          next.marker = { ...marker, color: tone };
        }
      }

      return next;
    }

    return trace;
  });
}

function Plot({ layout, config, data, ...rest }: PlotProps) {
  const safeLayout = (layout ?? {}) as Record<string, unknown>;
  const mergedLayout: Record<string, unknown> = {
    ...CHART_LAYOUT_BASE,
    ...safeLayout,
  };

  if (!("map" in safeLayout) && !("mapbox" in safeLayout)) {
    mergedLayout.xaxis = mergeAxisTheme((safeLayout.xaxis as Record<string, unknown>) ?? {});
    mergedLayout.yaxis = mergeAxisTheme((safeLayout.yaxis as Record<string, unknown>) ?? {});
    if ("yaxis2" in safeLayout) {
      mergedLayout.yaxis2 = mergeAxisTheme((safeLayout.yaxis2 as Record<string, unknown>) ?? {});
    }
  }

  return (
    <BasePlot
      {...rest}
      data={withSemanticTraceColors(data)}
      layout={mergedLayout}
      config={{ ...CHART_CONFIG_BASE, ...(config ?? {}) }}
    />
  );
}

function numberFmt(value: number): string {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value);
}

function readNum(item: Record<string, string | number>, key: string): number {
  const val = item[key];
  return typeof val === "number" ? val : Number(val);
}

function readStr(item: Record<string, string | number>, key: string): string {
  const val = item[key];
  return String(val ?? "");
}

function cityTrendColor(city: string): string | undefined {
  const normalizedCity = city.trim().toLowerCase();

  if (normalizedCity === "semi-urban" || normalizedCity === "semi urban") {
    return "#d97706";
  }

  if (normalizedCity === "urban") {
    return "#16a34a";
  }

  return undefined;
}

function monthlyOrderBarColors(values: number[]): string[] {
  const uniqueValues = Array.from(new Set(values)).sort((left, right) => right - left);
  const highestValue = uniqueValues[0];
  const secondHighestValue = uniqueValues[1];
  const lowestValue = uniqueValues[uniqueValues.length - 1];

  return values.map((value) => {
    if (value === highestValue) {
      return "#22c55e";
    }

    if (secondHighestValue !== undefined && value === secondHighestValue) {
      return "#fbbf24";
    }

    if (value === lowestValue) {
      return "#ef4444";
    }

    return "#60a5fa";
  });
}

function hourlyOrderGradientColors(values: number[]): string[] {
  const highestValue = Math.max(...values);
  const lowestValue = Math.min(...values);

  if (highestValue === lowestValue) {
    return values.map(() => "#22c55e");
  }

  return values.map((value) => {
    const ratio = (value - lowestValue) / (highestValue - lowestValue);
    const red = Math.round(239 - ratio * (239 - 34));
    const green = Math.round(68 + ratio * (197 - 68));
    const blue = Math.round(68 - ratio * (68 - 94));

    return `rgb(${red}, ${green}, ${blue})`;
  });
}

function cityOrderBandColors(values: number[]): string[] {
  const highestValue = Math.max(...values);
  const lowestValue = Math.min(...values);

  if (highestValue === lowestValue) {
    return values.map(() => "#22c55e");
  }

  return values.map((value) => {
    const ratio = (value - lowestValue) / (highestValue - lowestValue);

    if (ratio >= 0.66) {
      return "#22c55e";
    }

    if (ratio >= 0.33) {
      return "#facc15";
    }

    return "#ff3131";
  });
}

function cityOrderColors(cities: string[], values: number[]): string[] {
  const baseColors = cityOrderBandColors(values);

  return cities.map((city, idx) => {
    const normalizedCity = city.trim().toLowerCase();
    if (normalizedCity === "urban") {
      return "#facc15";
    }
    return baseColors[idx] ?? "#60a5fa";
  });
}

function festivalBarColors(values: string[]): string[] {
  return values.map((value) => {
    const normalizedValue = value.trim().toLowerCase();

    if (normalizedValue === "yes") {
      return "#39ff14";
    }

    if (normalizedValue === "no") {
      return "#ff3131";
    }

    return "#60a5fa";
  });
}

function weatherBarColors(values: string[]): string[] {
  const colorMap: Record<string, string> = {
    fog: "#B0BEC5",
    stormy: "#1A237E",
    cloudy: "#78909C",
    sandstorms: "#C19A6B",
    windy: "#42A5F5",
    sunny: "#FFB300",
  };

  return values.map((value) => colorMap[value.trim().toLowerCase()] ?? "#60a5fa");
}

function trafficBarColors(values: string[]): string[] {
  return values.map((value) => {
    const normalizedValue = value.trim().toLowerCase();

    if (normalizedValue === "low") {
      return "#1E8449";
    }

    if (normalizedValue === "medium") {
      return "#D68910";
    }

    if (normalizedValue === "high") {
      return "#922B21";
    }

    if (normalizedValue === "jam") {
      return "#641E16";
    }

    return "#60a5fa";
  });
}

function vehicleBarColors(values: string[]): string[] {
  const colorMap: Record<string, string> = {
    motorcycle: "#1F77B4",
    scooter: "#3498DB",
    electric_scooter: "#2ECC71",
    "electric scooter": "#2ECC71",
  };

  return values.map((value) => colorMap[value.trim().toLowerCase()] ?? "#60a5fa");
}

function orderTypeBarColors(values: string[]): string[] {
  const colorMap: Record<string, string> = {
    meal: "#D35400",
    buffet: "#8E44AD",
    snack: "#F39C12",
    drinks: "#3498DB",
  };

  return values.map((value) => colorMap[value.trim().toLowerCase()] ?? "#60a5fa");
}

function avgDistanceCityColors(values: string[]): string[] {
  return values.map((value) => {
    const normalizedValue = value.trim().toLowerCase();

    if (normalizedValue === "semi-urban" || normalizedValue === "semi urban") {
      return "#22c55e";
    }

    if (normalizedValue === "urban") {
      return "#facc15";
    }

    if (normalizedValue === "metropolitan" || normalizedValue === "metropolitian") {
      return "#f59e0b";
    }

    return "#60a5fa";
  });
}

function toggleValue(current: string[], value: string): string[] {
  return current.includes(value) ? current.filter((item) => item !== value) : [...current, value];
}

function App() {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<PageName>("Executive Overview");

  const [threshold, setThreshold] = useState(30);
  const [cities, setCities] = useState<string[]>([]);
  const [weather, setWeather] = useState<string[]>([]);
  const [traffic, setTraffic] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState<[number, number]>([0, 60]);

  const [executive, setExecutive] = useState<ExecutiveOverviewResponse | null>(null);
  const [deliveryOps, setDeliveryOps] = useState<DeliveryOperationsResponse | null>(null);
  const [riderEff, setRiderEff] = useState<RiderEfficiencyResponse | null>(null);
  const [demandTime, setDemandTimeData] = useState<DemandTimeResponse | null>(null);
  const [externalImpact, setExternalImpact] = useState<ExternalImpactResponse | null>(null);
  const [locationIntel, setLocationIntel] = useState<LocationIntelligenceResponse | null>(null);
  const [predictiveAssets, setPredictiveAssets] = useState<PredictiveAssetsResponse | null>(null);

  const [prediction, setPrediction] = useState<{ time: number; delay: number } | null>(null);
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  const [isCityDropdownOpen, setIsCityDropdownOpen] = useState(false);
  const [isWeatherDropdownOpen, setIsWeatherDropdownOpen] = useState(false);
  const [isTrafficDropdownOpen, setIsTrafficDropdownOpen] = useState(false);
  const cityDropdownRef = useRef<HTMLDivElement | null>(null);
  const weatherDropdownRef = useRef<HTMLDivElement | null>(null);
  const trafficDropdownRef = useRef<HTMLDivElement | null>(null);

  const [predForm, setPredForm] = useState<Record<string, string | number>>({
    weather_conditions: "",
    road_traffic_density: "",
    city: "",
    festival: "",
    vehicle_condition: 2,
    type_of_order: "",
    type_of_vehicle: "",
    multiple_deliveries: 1,
    delivery_person_ratings: 4.2,
    delivery_person_age: 28,
    distance_km: 7.5,
  });

  const indiaMapLayout = {
    mapbox: {
      style: "open-street-map",
      center: { lat: 22.9734, lon: 78.6569 },
      zoom: 4.2,
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    font: { color: "#0f172a" },
    dragmode: "zoom",
    margin: { l: 0, r: 0, t: 20, b: 0 },
    uirevision: "india-map",
  } as const;

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        const opts = await getFilterOptions(threshold);
        setOptions(opts);
        setCities(opts.cities);
        setWeather(opts.weather);
        setTraffic(opts.traffic);
        setTimeRange([opts.time_min, opts.time_max]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load filter options");
      } finally {
        setLoading(false);
      }
    };
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filters: FiltersRequest = useMemo(
    () => ({
      on_time_threshold: threshold,
      cities,
      weather,
      traffic,
      time_min: timeRange[0],
      time_max: timeRange[1],
    }),
    [threshold, cities, weather, traffic, timeRange]
  );

  useEffect(() => {
    if (!options) {
      return;
    }

    const run = async () => {
      try {
        setLoading(true);
        setError(null);

        if (page === "Executive Overview") {
          setExecutive(await getExecutiveOverview(filters));
        } else if (page === "Delivery Operations") {
          setDeliveryOps(await getDeliveryOperations(filters));
        } else if (page === "Rider Efficiency") {
          setRiderEff(await getRiderEfficiency(filters));
        } else if (page === "Demand & Time Analysis") {
          setDemandTimeData(await getDemandTime(filters));
        } else if (page === "External Impact Analysis") {
          setExternalImpact(await getExternalImpact(filters));
        } else if (page === "Location Intelligence") {
          setLocationIntel(await getLocationIntelligence(filters));
        } else if (page === "Predictive Analytics") {
          const assets = await getPredictiveAssets(filters);
          setPredictiveAssets(assets);
          if (!predForm.weather_conditions && assets.options.weather_conditions.length > 0) {
            setPredForm((prev) => ({
              ...prev,
              weather_conditions: assets.options.weather_conditions[0],
              road_traffic_density: assets.options.road_traffic_density[0] ?? "",
              city: assets.options.city[0] ?? "",
              festival: assets.options.festival[0] ?? "",
              type_of_order: assets.options.type_of_order[0] ?? "",
              type_of_vehicle: assets.options.type_of_vehicle[0] ?? "",
            }));
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load page");
      } finally {
        setLoading(false);
      }
    };

    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options, filters, page]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (cityDropdownRef.current && !cityDropdownRef.current.contains(event.target as Node)) {
        setIsCityDropdownOpen(false);
      }

      if (weatherDropdownRef.current && !weatherDropdownRef.current.contains(event.target as Node)) {
        setIsWeatherDropdownOpen(false);
      }

      if (trafficDropdownRef.current && !trafficDropdownRef.current.contains(event.target as Node)) {
        setIsTrafficDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const runPrediction = async () => {
    try {
      const result = await predictDelivery(predForm);
      setPrediction({ time: result.predicted_delivery_time, delay: result.delay_probability });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    }
  };

  return (
    <div className="page">
      <div className="aurora" />
      <header className="topbar">
        <h1>Zomato Delivery Intelligence Dashboard and Analytics</h1>
        <p>Real-time performance analytics & delivery insights</p>
        <button
          type="button"
          className="filter-toggle-btn"
          onClick={() => setIsFilterPanelOpen(true)}
          aria-label="Open filters panel"
        >
          Open Filters
        </button>
      </header>

      <section className="layout">
        <div
          className={`filter-panel-backdrop ${isFilterPanelOpen ? "show" : ""}`}
          onClick={() => setIsFilterPanelOpen(false)}
          aria-hidden="true"
        />
        <aside className={`panel controls ${isFilterPanelOpen ? "open" : ""}`}>
          <div className="controls-header">
            <h2>Filters</h2>
            <button
              type="button"
              className="filter-close-btn"
              onClick={() => setIsFilterPanelOpen(false)}
              aria-label="Close filters panel"
            >
              x
            </button>
          </div>
          <label>
            On-time Threshold: {threshold} min
            <input
              type="range"
              min={20}
              max={45}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            />
          </label>

          <label>
            City
            <div ref={cityDropdownRef} className={`city-dropdown ${isCityDropdownOpen ? "show" : ""}`}>
              <button
                type="button"
                className="city-dropdown-btn"
                onClick={() => setIsCityDropdownOpen((prev) => !prev)}
                aria-expanded={isCityDropdownOpen}
                aria-controls="city-dropdown-content"
              >
                Select cities
                <span aria-hidden="true">▼</span>
              </button>
              <div id="city-dropdown-content" className="city-options" role="group" aria-label="City options">
                {(options?.cities ?? []).map((c) => {
                  const id = `city-${c.replace(/\s+/g, "-").toLowerCase()}`;
                  return (
                    <label key={c} htmlFor={id} className="city-option-item">
                      <input
                        id={id}
                        type="checkbox"
                        checked={cities.includes(c)}
                        onChange={() => setCities((prev) => toggleValue(prev, c))}
                      />
                      <span>{c}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </label>

          <label>
            Weather
            <div ref={weatherDropdownRef} className={`city-dropdown ${isWeatherDropdownOpen ? "show" : ""}`}>
              <button
                type="button"
                className="city-dropdown-btn"
                onClick={() => setIsWeatherDropdownOpen((prev) => !prev)}
                aria-expanded={isWeatherDropdownOpen}
                aria-controls="weather-dropdown-content"
              >
                Select weather
                <span aria-hidden="true">▼</span>
              </button>
              <div id="weather-dropdown-content" className="city-options" role="group" aria-label="Weather options">
                {(options?.weather ?? []).map((w) => {
                  const id = `weather-${w.replace(/\s+/g, "-").toLowerCase()}`;
                  return (
                    <label key={w} htmlFor={id} className="city-option-item">
                      <input
                        id={id}
                        type="checkbox"
                        checked={weather.includes(w)}
                        onChange={() => setWeather((prev) => toggleValue(prev, w))}
                      />
                      <span>{w}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </label>

          <label>
            Traffic
            <div ref={trafficDropdownRef} className={`city-dropdown ${isTrafficDropdownOpen ? "show" : ""}`}>
              <button
                type="button"
                className="city-dropdown-btn"
                onClick={() => setIsTrafficDropdownOpen((prev) => !prev)}
                aria-expanded={isTrafficDropdownOpen}
                aria-controls="traffic-dropdown-content"
              >
                Select traffic
                <span aria-hidden="true">▼</span>
              </button>
              <div id="traffic-dropdown-content" className="city-options" role="group" aria-label="Traffic options">
                {(options?.traffic ?? []).map((t) => {
                  const id = `traffic-${t.replace(/\s+/g, "-").toLowerCase()}`;
                  return (
                    <label key={t} htmlFor={id} className="city-option-item">
                      <input
                        id={id}
                        type="checkbox"
                        checked={traffic.includes(t)}
                        onChange={() => setTraffic((prev) => toggleValue(prev, t))}
                      />
                      <span>{t}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </label>

          <label>
            Time Min
            <input
              type="number"
              value={timeRange[0]}
              onChange={(e) => setTimeRange([Number(e.target.value), timeRange[1]])}
            />
          </label>

          <label>
            Time Max
            <input
              type="number"
              value={timeRange[1]}
              onChange={(e) => setTimeRange([timeRange[0], Number(e.target.value)])}
            />
          </label>

          <button
            type="button"
            onClick={() => {
              if (!options) return;
              setCities(options.cities);
              setWeather(options.weather);
              setTraffic(options.traffic);
              setTimeRange([options.time_min, options.time_max]);
              setThreshold(30);
            }}
          >
            Reset All Filters
          </button>
        </aside>

        <main className="panel content">
          <nav className="tabbar">
            {PAGES.map((p) => (
              <button key={p} type="button" className={page === p ? "active" : ""} onClick={() => setPage(p)}>
                {p}
              </button>
            ))}
          </nav>

          {loading && <p>Loading...</p>}
          {error && <p className="error">{error}</p>}

          {page === "Executive Overview" && executive && (
            <>
              <div className="metrics">
                <article><h3>Total Orders</h3><strong>{numberFmt(executive.metrics.total_orders)}</strong></article>
                <article><h3>Average Delivery Time</h3><strong>{numberFmt(executive.metrics.avg_delivery_time)} min</strong></article>
                <article><h3>On-Time %</h3><strong>{numberFmt(executive.metrics.on_time_pct)}%</strong></article>
                <article><h3>Average Rider Rating</h3><strong>{numberFmt(executive.metrics.avg_rating)}</strong></article>
              </div>
              <div className="charts">
                <section>
                  <h3>Orders Trend (by Date)</h3>
                  <Plot data={[{ x: executive.trend.map((d) => d.order_date), y: executive.trend.map((d) => d.orders), type: "scatter", mode: "lines+markers", line: { color: "#39ff14" }, marker: { color: "#39ff14" } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} />
                </section>
                <section>
                  <h3>Orders by City</h3>
                  <Plot data={[{ x: executive.city_orders.map((d) => d.city), y: executive.city_orders.map((d) => d.orders), type: "bar", marker: { color: cityOrderColors(executive.city_orders.map((d) => d.city), executive.city_orders.map((d) => d.orders)) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} />
                </section>
              </div>
            </>
          )}

          {page === "Delivery Operations" && deliveryOps && (
            <div className="charts">
              <section><h3>Avg Delivery Time by City</h3><Plot data={[{ x: deliveryOps.city_time.map((d) => readStr(d, "City")), y: deliveryOps.city_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: cityOrderColors(deliveryOps.city_time.map((d) => readStr(d, "City")), deliveryOps.city_time.map((d) => readNum(d, "Time_taken (min)"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Weather</h3><Plot data={[{ x: deliveryOps.weather_time.map((d) => readStr(d, "Weather_conditions")), y: deliveryOps.weather_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: weatherBarColors(deliveryOps.weather_time.map((d) => readStr(d, "Weather_conditions"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Traffic Density</h3><Plot data={[{ x: deliveryOps.traffic_time.map((d) => readStr(d, "Road_traffic_density")), y: deliveryOps.traffic_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: trafficBarColors(deliveryOps.traffic_time.map((d) => readStr(d, "Road_traffic_density"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Vehicle Type</h3><Plot data={[{ x: deliveryOps.vehicle_time.map((d) => readStr(d, "Type_of_vehicle")), y: deliveryOps.vehicle_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: vehicleBarColors(deliveryOps.vehicle_time.map((d) => readStr(d, "Type_of_vehicle"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Type of Order</h3><Plot data={[{ x: deliveryOps.order_type_time.map((d) => readStr(d, "Type_of_order")), y: deliveryOps.order_type_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: orderTypeBarColors(deliveryOps.order_type_time.map((d) => readStr(d, "Type_of_order"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Distance vs Delivery Time</h3><Plot data={[{ x: deliveryOps.distance_scatter.map((d) => readNum(d, "distance_km")), y: deliveryOps.distance_scatter.map((d) => readNum(d, "Time_taken (min)")), mode: "markers", type: "scatter" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Distance per City</h3><Plot data={[{ x: deliveryOps.avg_dist_city.map((d) => readStr(d, "City")), y: deliveryOps.avg_dist_city.map((d) => readNum(d, "distance_km")), type: "bar", marker: { color: avgDistanceCityColors(deliveryOps.avg_dist_city.map((d) => readStr(d, "City"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Distance Category</h3><Plot data={[{ labels: deliveryOps.distance_category.map((d) => readStr(d, "distance_category")), values: deliveryOps.distance_category.map((d) => readNum(d, "orders")), type: "pie" }]} layout={{ margin: { l: 20, r: 20, t: 10, b: 20 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
            </div>
          )}

          {page === "Rider Efficiency" && riderEff && (
            <>
              <div className="metrics">
                <article><h3>Total Riders</h3><strong>{numberFmt(riderEff.metrics.total_riders)}</strong></article>
                <article><h3>Avg Orders/Rider</h3><strong>{numberFmt(riderEff.metrics.avg_orders_per_rider)}</strong></article>
                <article><h3>Avg Delivery Time/Rider</h3><strong>{numberFmt(riderEff.metrics.avg_delivery_time_per_rider)} min</strong></article>
                <article><h3>Avg On-Time %</h3><strong>{numberFmt(riderEff.metrics.avg_on_time_pct)}%</strong></article>
              </div>
              <div className="charts">
                <section><h3>Top 10 Riders by Efficiency</h3><Plot data={[{ x: riderEff.top10.map((d) => readNum(d, "efficiency_score")), y: riderEff.top10.map((d) => readStr(d, "Delivery_person_ID")), type: "bar", orientation: "h", marker: { color: "#2ECC71" } }]} layout={{ margin: { l: 100, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Bottom 10 Riders</h3><Plot data={[{ x: riderEff.bottom10.map((d) => readNum(d, "efficiency_score")), y: riderEff.bottom10.map((d) => readStr(d, "Delivery_person_ID")), type: "bar", orientation: "h", marker: { color: "#E74C3C" } }]} layout={{ margin: { l: 100, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Delivery Time vs Rider Rating</h3><Plot data={[{ x: riderEff.rating_vs_time.map((d) => readNum(d, "avg_rating")), y: riderEff.rating_vs_time.map((d) => readNum(d, "avg_delivery_time")), mode: "markers", type: "scatter" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Age vs Performance Analysis</h3><Plot data={[{ x: riderEff.age_vs_perf.map((d) => readNum(d, "avg_age")), y: riderEff.age_vs_perf.map((d) => readNum(d, "avg_delivery_time")), mode: "markers", type: "scatter" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Orders Completed by Rider (Top 30)</h3><Plot data={[{ x: riderEff.orders_by_rider.map((d) => readStr(d, "Delivery_person_ID")), y: riderEff.orders_by_rider.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Efficiency Score Distribution</h3><Plot data={[{ x: riderEff.efficiency_hist.bins, y: riderEff.efficiency_hist.counts, type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              </div>
              <section className="table-section">
                <h3>Rider Ranking Table</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Rider ID</th>
                        <th>Orders</th>
                        <th>Avg Delivery Time</th>
                        <th>On-Time %</th>
                        <th>Efficiency Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riderEff.ranking.slice(0, 100).map((row, idx) => (
                        <tr key={`${readStr(row, "Delivery_person_ID")}-${idx}`}>
                          <td>{readStr(row, "Delivery_person_ID")}</td>
                          <td>{numberFmt(readNum(row, "orders"))}</td>
                          <td>{numberFmt(readNum(row, "avg_delivery_time"))}</td>
                          <td>{numberFmt(readNum(row, "on_time_pct"))}</td>
                          <td>{numberFmt(readNum(row, "efficiency_score"))}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {page === "Demand & Time Analysis" && demandTime && (
            <div className="charts">
              <section><h3>Orders per Day</h3><Plot data={[{ x: demandTime.daily.map((d) => readStr(d, "Order_Date")), y: demandTime.daily.map((d) => readNum(d, "orders")), type: "scatter", mode: "lines+markers", line: { color: "#22c55e" }, marker: { color: "#22c55e" } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Orders per Month</h3><Plot data={[{ x: demandTime.monthly.map((d) => readStr(d, "order_month")), y: demandTime.monthly.map((d) => readNum(d, "orders")), type: "bar", marker: { color: monthlyOrderBarColors(demandTime.monthly.map((d) => readNum(d, "orders"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Orders per Hour</h3><Plot data={[{ x: demandTime.hourly.map((d) => readNum(d, "order_hour")), y: demandTime.hourly.map((d) => readNum(d, "orders")), type: "bar", marker: { color: hourlyOrderGradientColors(demandTime.hourly.map((d) => readNum(d, "orders"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Peak Hours (Top 5)</h3><Plot data={[{ x: demandTime.peak_hours.map((d) => readNum(d, "order_hour")), y: demandTime.peak_hours.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Festival vs Normal Day Order Comparison</h3><Plot data={[{ x: demandTime.festival_cmp.map((d) => readStr(d, "Festival")), y: demandTime.festival_cmp.map((d) => readNum(d, "orders")), type: "bar", marker: { color: festivalBarColors(demandTime.festival_cmp.map((d) => readStr(d, "Festival"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>City-wise Demand Trend</h3><Plot data={Array.from(new Set(demandTime.city_trend.map((d) => readStr(d, "City")))).map((city) => ({ name: city, x: demandTime.city_trend.filter((d) => readStr(d, "City") === city).map((d) => readStr(d, "Order_Date")), y: demandTime.city_trend.filter((d) => readStr(d, "City") === city).map((d) => readNum(d, "orders")), type: "scatter", mode: "lines", line: cityTrendColor(city) ? { color: cityTrendColor(city) } : undefined }))} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
            </div>
          )}

          {page === "External Impact Analysis" && externalImpact && (
            <div className="charts">
              <section><h3>Weather vs Delivery Time</h3><Plot data={[{ x: externalImpact.weather_vs_time.map((d) => readStr(d, "Weather_conditions")), y: externalImpact.weather_vs_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: weatherBarColors(externalImpact.weather_vs_time.map((d) => readStr(d, "Weather_conditions"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Traffic Density vs Delivery Time</h3><Plot data={[{ x: externalImpact.traffic_vs_time.map((d) => readStr(d, "Road_traffic_density")), y: externalImpact.traffic_vs_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: trafficBarColors(externalImpact.traffic_vs_time.map((d) => readStr(d, "Road_traffic_density"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Festival Impact on Delivery Time</h3><Plot data={[{ x: externalImpact.festival_impact.map((d) => readStr(d, "Festival")), y: externalImpact.festival_impact.map((d) => readNum(d, "Time_taken (min)")), type: "bar", marker: { color: festivalBarColors(externalImpact.festival_impact.map((d) => readStr(d, "Festival"))) } }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section>
                <h3>Vehicle Condition vs Performance</h3>
                <Plot
                  data={[
                    { x: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "Vehicle_condition")), y: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "avg_delivery_time")), type: "bar", name: "Avg Delivery Time" },
                    { x: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "Vehicle_condition")), y: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "on_time_pct")), type: "scatter", mode: "lines+markers", yaxis: "y2", name: `On-Time % (<= ${externalImpact.on_time_threshold} min)`, line: { color: "#22c55e" }, marker: { color: "#22c55e" } },
                  ]}
                  layout={{ margin: { l: 40, r: 40, t: 10, b: 40 }, yaxis2: { overlaying: "y", side: "right" } }}
                  style={{ width: "100%", height: 320 }}
                  config={{ displayModeBar: false, responsive: true }}
                />
              </section>
            </div>
          )}

          {page === "Location Intelligence" && locationIntel && (
            <div className="charts">
              <section>
                <h3>Delivery Density Map (India)</h3>
                <Plot
                  data={[
                    {
                      lat: locationIntel.density.map((d) => readNum(d, "Restaurant_latitude")),
                      lon: locationIntel.density.map((d) => readNum(d, "Restaurant_longitude")),
                      mode: "markers",
                      type: "scattermapbox",
                      marker: { size: 6, opacity: 0.75 },
                    },
                  ]}
                  layout={indiaMapLayout}
                  style={{ width: "100%", height: 360 }}
                  config={{ displayModeBar: true, responsive: true, scrollZoom: true }}
                />
              </section>
              <section>
                <h3>High Delay Zones (India)</h3>
                <Plot
                  data={[
                    {
                      lat: locationIntel.delay_zones.map((d) => readNum(d, "Delivery_location_latitude")),
                      lon: locationIntel.delay_zones.map((d) => readNum(d, "Delivery_location_longitude")),
                      mode: "markers",
                      type: "scattermapbox",
                      marker: { size: 6, color: "#ef4444", opacity: 0.78 },
                    },
                  ]}
                  layout={indiaMapLayout}
                  style={{ width: "100%", height: 360 }}
                  config={{ displayModeBar: true, responsive: true, scrollZoom: true }}
                />
              </section>
              <section>
                <h3>Avg Delivery Time Map (India)</h3>
                <Plot
                  data={[
                    {
                      lat: locationIntel.avg_map.map((d) => readNum(d, "grid_lat")),
                      lon: locationIntel.avg_map.map((d) => readNum(d, "grid_lon")),
                      mode: "markers",
                      type: "scattermapbox",
                      marker: {
                        size: locationIntel.avg_map.map((d) => Math.max(4, readNum(d, "orders") / 8)),
                        color: locationIntel.avg_map.map((d) => readNum(d, "avg_time")),
                        colorscale: [[0, "#dbeafe"], [0.5, "#60a5fa"], [1, "#1e3a8a"]],
                        showscale: true,
                        opacity: 0.82,
                      },
                    },
                  ]}
                  layout={indiaMapLayout}
                  style={{ width: "100%", height: 360 }}
                  config={{ displayModeBar: true, responsive: true, scrollZoom: true }}
                />
              </section>
              <section>
                <h3>Order Distribution Map (India)</h3>
                <Plot
                  data={[
                    {
                      lat: locationIntel.distribution_points.map((d) => readNum(d, "lat")),
                      lon: locationIntel.distribution_points.map((d) => readNum(d, "lon")),
                      mode: "markers",
                      type: "scattermapbox",
                      marker: { size: 4, opacity: 0.5, color: "#1e3a8a" },
                    },
                  ]}
                  layout={indiaMapLayout}
                  style={{ width: "100%", height: 360 }}
                  config={{ displayModeBar: true, responsive: true, scrollZoom: true }}
                />
              </section>
            </div>
          )}

          {page === "Predictive Analytics" && predictiveAssets && (
            <>
              <div className="metrics">
                <article><h3>Regression R2</h3><strong>{numberFmt(predictiveAssets.r2)}</strong></article>
                <article><h3>Regression MAE</h3><strong>{numberFmt(predictiveAssets.mae)} min</strong></article>
                <article><h3>Predicted Time</h3><strong>{prediction ? `${numberFmt(prediction.time)} min` : "-"}</strong></article>
                <article><h3>Delay Probability</h3><strong>{prediction ? `${numberFmt(prediction.delay)}%` : "-"}</strong></article>
              </div>

              <div className="pred-form">
                <label className="pred-field">Weather
                  <select value={String(predForm.weather_conditions)} onChange={(e) => setPredForm((p) => ({ ...p, weather_conditions: e.target.value }))}>{predictiveAssets.options.weather_conditions.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <label className="pred-field">Traffic Density
                  <select value={String(predForm.road_traffic_density)} onChange={(e) => setPredForm((p) => ({ ...p, road_traffic_density: e.target.value }))}>{predictiveAssets.options.road_traffic_density.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <label className="pred-field">City
                  <select value={String(predForm.city)} onChange={(e) => setPredForm((p) => ({ ...p, city: e.target.value }))}>{predictiveAssets.options.city.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <label className="pred-field">Festival
                  <select value={String(predForm.festival)} onChange={(e) => setPredForm((p) => ({ ...p, festival: e.target.value }))}>{predictiveAssets.options.festival.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <label className="pred-field">Type of Order
                  <select value={String(predForm.type_of_order)} onChange={(e) => setPredForm((p) => ({ ...p, type_of_order: e.target.value }))}>{predictiveAssets.options.type_of_order.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <label className="pred-field">Type of Vehicle
                  <select value={String(predForm.type_of_vehicle)} onChange={(e) => setPredForm((p) => ({ ...p, type_of_vehicle: e.target.value }))}>{predictiveAssets.options.type_of_vehicle.map((o) => <option key={o} value={o}>{o}</option>)}</select>
                </label>
                <button type="button" onClick={runPrediction}>Predict Delivery</button>
              </div>

              <div className="charts">
                <section><h3>Feature Importance (Regression)</h3><Plot data={[{ x: predictiveAssets.reg_importances.map((d) => readNum(d, "importance")), y: predictiveAssets.reg_importances.map((d) => readStr(d, "feature")), type: "bar", orientation: "h" }]} layout={{ margin: { l: 180, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 360 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Feature Importance (Classification)</h3><Plot data={[{ x: predictiveAssets.cls_importances.map((d) => readNum(d, "importance")), y: predictiveAssets.cls_importances.map((d) => readStr(d, "feature")), type: "bar", orientation: "h" }]} layout={{ margin: { l: 180, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 360 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section>
                  <h3>Confusion Matrix</h3>
                  <Plot
                    data={[
                      {
                        z: predictiveAssets.confusion_matrix,
                        x: ["Predicted On-Time", "Predicted Delayed"],
                        y: ["Actual On-Time", "Actual Delayed"],
                        type: "heatmap",
                        colorscale: [[0, "#dbeafe"], [0.5, "#60a5fa"], [1, "#1e3a8a"]],
                        showscale: true,
                        hovertemplate: "Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
                      },
                    ]}
                    layout={{
                      margin: { l: 40, r: 20, t: 10, b: 40 },
                      xaxis: { title: { text: "Predicted Class" } },
                      yaxis: { title: { text: "Actual Class" } },
                    }}
                    style={{ width: "100%", height: 360 }}
                    config={{ displayModeBar: false, responsive: true }}
                  />
                </section>
              </div>
            </>
          )}
        </main>
      </section>
    </div>
  );
}

export default App;
