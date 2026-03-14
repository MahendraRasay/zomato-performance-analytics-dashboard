import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
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

function toSelectValues(select: HTMLSelectElement): string[] {
  return Array.from(select.selectedOptions).map((o) => o.value);
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
    map: {
      style: "open-street-map",
      center: { lat: 22.9734, lon: 78.6569 },
      zoom: 4.2,
    },
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
        <h1>Zomato Delivery Intelligence Dashboard</h1>
        <p>React parity migration from Streamlit pages and analytics flow</p>
      </header>

      <section className="layout">
        <aside className="panel controls">
          <h2>Filters</h2>
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
            <select multiple value={cities} onChange={(e) => setCities(toSelectValues(e.target))}>
              {(options?.cities ?? []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>

          <label>
            Weather
            <select multiple value={weather} onChange={(e) => setWeather(toSelectValues(e.target))}>
              {(options?.weather ?? []).map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </label>

          <label>
            Traffic
            <select multiple value={traffic} onChange={(e) => setTraffic(toSelectValues(e.target))}>
              {(options?.traffic ?? []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
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
                  <Plot data={[{ x: executive.trend.map((d) => d.order_date), y: executive.trend.map((d) => d.orders), type: "scatter", mode: "lines+markers" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} />
                </section>
                <section>
                  <h3>Orders by City</h3>
                  <Plot data={[{ x: executive.city_orders.map((d) => d.city), y: executive.city_orders.map((d) => d.orders), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} />
                </section>
              </div>
            </>
          )}

          {page === "Delivery Operations" && deliveryOps && (
            <div className="charts">
              <section><h3>Avg Delivery Time by City</h3><Plot data={[{ x: deliveryOps.city_time.map((d) => readStr(d, "City")), y: deliveryOps.city_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Weather</h3><Plot data={[{ x: deliveryOps.weather_time.map((d) => readStr(d, "Weather_conditions")), y: deliveryOps.weather_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Traffic Density</h3><Plot data={[{ x: deliveryOps.traffic_time.map((d) => readStr(d, "Road_traffic_density")), y: deliveryOps.traffic_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Vehicle Type</h3><Plot data={[{ x: deliveryOps.vehicle_time.map((d) => readStr(d, "Type_of_vehicle")), y: deliveryOps.vehicle_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Delivery Time by Type of Order</h3><Plot data={[{ x: deliveryOps.order_type_time.map((d) => readStr(d, "Type_of_order")), y: deliveryOps.order_type_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Distance vs Delivery Time</h3><Plot data={[{ x: deliveryOps.distance_scatter.map((d) => readNum(d, "distance_km")), y: deliveryOps.distance_scatter.map((d) => readNum(d, "Time_taken (min)")), mode: "markers", type: "scatter" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Avg Distance per City</h3><Plot data={[{ x: deliveryOps.avg_dist_city.map((d) => readStr(d, "City")), y: deliveryOps.avg_dist_city.map((d) => readNum(d, "distance_km")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
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
                <section><h3>Top 10 Riders by Efficiency</h3><Plot data={[{ x: riderEff.top10.map((d) => readNum(d, "efficiency_score")), y: riderEff.top10.map((d) => readStr(d, "Delivery_person_ID")), type: "bar", orientation: "h" }]} layout={{ margin: { l: 100, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
                <section><h3>Bottom 10 Riders</h3><Plot data={[{ x: riderEff.bottom10.map((d) => readNum(d, "efficiency_score")), y: riderEff.bottom10.map((d) => readStr(d, "Delivery_person_ID")), type: "bar", orientation: "h" }]} layout={{ margin: { l: 100, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
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
              <section><h3>Orders per Day</h3><Plot data={[{ x: demandTime.daily.map((d) => readStr(d, "Order_Date")), y: demandTime.daily.map((d) => readNum(d, "orders")), type: "scatter", mode: "lines+markers" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Orders per Month</h3><Plot data={[{ x: demandTime.monthly.map((d) => readStr(d, "order_month")), y: demandTime.monthly.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Orders per Hour</h3><Plot data={[{ x: demandTime.hourly.map((d) => readNum(d, "order_hour")), y: demandTime.hourly.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Peak Hours (Top 5)</h3><Plot data={[{ x: demandTime.peak_hours.map((d) => readNum(d, "order_hour")), y: demandTime.peak_hours.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Festival vs Normal Day Order Comparison</h3><Plot data={[{ x: demandTime.festival_cmp.map((d) => readStr(d, "Festival")), y: demandTime.festival_cmp.map((d) => readNum(d, "orders")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>City-wise Demand Trend</h3><Plot data={Array.from(new Set(demandTime.city_trend.map((d) => readStr(d, "City")))).map((city) => ({ name: city, x: demandTime.city_trend.filter((d) => readStr(d, "City") === city).map((d) => readStr(d, "Order_Date")), y: demandTime.city_trend.filter((d) => readStr(d, "City") === city).map((d) => readNum(d, "orders")), type: "scatter", mode: "lines" }))} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
            </div>
          )}

          {page === "External Impact Analysis" && externalImpact && (
            <div className="charts">
              <section><h3>Weather vs Delivery Time</h3><Plot data={[{ x: externalImpact.weather_vs_time.map((d) => readStr(d, "Weather_conditions")), y: externalImpact.weather_vs_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Traffic Density vs Delivery Time</h3><Plot data={[{ x: externalImpact.traffic_vs_time.map((d) => readStr(d, "Road_traffic_density")), y: externalImpact.traffic_vs_time.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 70 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section><h3>Festival Impact on Delivery Time</h3><Plot data={[{ x: externalImpact.festival_impact.map((d) => readStr(d, "Festival")), y: externalImpact.festival_impact.map((d) => readNum(d, "Time_taken (min)")), type: "bar" }]} layout={{ margin: { l: 40, r: 20, t: 10, b: 40 } }} style={{ width: "100%", height: 320 }} config={{ displayModeBar: false, responsive: true }} /></section>
              <section>
                <h3>Vehicle Condition vs Performance</h3>
                <Plot
                  data={[
                    { x: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "Vehicle_condition")), y: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "avg_delivery_time")), type: "bar", name: "Avg Delivery Time" },
                    { x: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "Vehicle_condition")), y: externalImpact.vehicle_condition_perf.map((d) => readNum(d, "on_time_pct")), type: "scatter", mode: "lines+markers", yaxis: "y2", name: `On-Time % (<= ${externalImpact.on_time_threshold} min)` },
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
                      type: "scattermap",
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
                      type: "scattermap",
                      marker: { size: 6, color: "#ef476f", opacity: 0.78 },
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
                      type: "scattermap",
                      marker: {
                        size: locationIntel.avg_map.map((d) => Math.max(4, readNum(d, "orders") / 8)),
                        color: locationIntel.avg_map.map((d) => readNum(d, "avg_time")),
                        colorscale: "YlOrRd",
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
                      type: "scattermap",
                      marker: { size: 4, opacity: 0.5, color: "#006d77" },
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
