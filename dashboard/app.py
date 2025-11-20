import random
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import altair as alt
import calendar
import pydeck as pdk
import geopandas as gpd
import streamlit.components.v1 as components
from shapely.geometry import LineString
import json


# =======================
# PAGE SETUP
# =======================
st.set_page_config(
    page_title="DT Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =======================
# THEME / STYLES
# =======================
st.markdown("""
<style>
/* ========== BASE COLORS ========== */
[data-testid="AppViewContainer"],
[data-testid="stAppViewContainer"] {
  background-color:#0e1117;
  color:#fafafa;
}

/* ========== ROOT ========== */
/* Make the row that wraps the columns fill the viewport */
.root-row {
  display: flex;
  align-items: stretch;
  min-height: calc(100vh - 2rem);  /* tweak 2rem if needed */
}

/* Make each Streamlit column a flex column that stretches */
.root-row [data-testid="column"] {
  display: flex;
  flex-direction: column;
}

/* Let the first child container in each column stretch */
.root-row [data-testid="column"] > div {
  flex: 1 1 auto;
}

/* ========== SIDEBAR ========== */

/* SIDEBAR LOOK & SCALE */
[data-testid="stSidebar"] {
  background-color:#40444d;
  font-size:1rem;         /* smaller everything */
  padding-left:0.7rem !important;
  padding-right:0.7rem !important;
}

/* Section titles */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-size:1rem !important;
  margin-bottom:0.3rem !important;
}

/* Radio / checkbox text */
[data-testid="stSidebar"] label {
  font-size:0.75rem !important;
  margin-bottom:0.05rem !important;
}

/* Paragraph text */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  font-size:0.78rem !important;
  margin-bottom:0.2rem !important;
}

/* Reduce all vertical padding inside sidebar */
[data-testid="stSidebar"] > div {
  padding-top:0.3rem !important;
  padding-bottom:0.3rem !important;
}

/* Shrink expander spacing */
.streamlit-expanderHeader {
  font-size:0.8rem !important;
  padding-top:0.2rem !important;
  padding-bottom:0.2rem !important;
}

.streamlit-expanderContent {
  padding-top:0.2rem !important;
  padding-bottom:0.2rem !important;
}

/* Remove large gaps between sidebar elements */
[data-testid="stSidebar"] .block-container {
  gap:0 !important;
}

[data-testid="stSidebar"] > div > div {
  margin-bottom:0.4rem !important;
}

.dashboard-box h4,
.dashboard-box li,
.dashboard-box p {
  color:#ffffff !important;
}

/* ========== TOOLTIP ========== */
.tooltip { position:relative; display:inline-block; cursor:pointer; }
.tooltiptext {
  visibility:hidden;
  width:260px;
  background:#333;
  color:#fff;
  text-align:left;
  border-radius:6px;
  padding:10px;
  position:absolute;
  z-index:1;
  top:100%;
  left:50%;
  transform:translateX(-50%);
  opacity:0;
  transition:opacity .3s;
  font-size:13px;
  box-shadow:0 0 10px rgba(0,0,0,.5);
}
.tooltip:hover .tooltiptext { visibility:visible; opacity:1; }

/* ========== LAYOUT / GLOBAL SCALE ========== */
.block-container {
  padding-top:2rem !important;
  margin-top:0 !important;
}

[data-testid="stAppViewContainer"] > .main {
  padding-top:0 !important;
  margin-top:0 !important;
  max-width:1600px;
  margin-left:auto;
  margin-right:auto;
}

html, body, [data-testid="stAppViewContainer"] {
  font-size:14px;
}

/* ========== KPI CARD STYLE ========== */
.dt-kpi-card {
  background:#26264d;
  padding:10px 12px;
  border-radius:10px;
  min-height:95px;      /* controls vertical size per card */
  display:flex;
  flex-direction:column;
  justify-content:center;
  margin-bottom:8px;    /* spacing between cards */
}
.dt-kpi-card h6 {
  font-size:0.85rem;
  margin:0 0 4px 0;
  color:#A3A6F7;
}
.dt-kpi-card p {
  font-size:1.2rem;
  margin:0;
  font-weight:bold;
  color:#ffffff;
}
.dt-kpi-card span {
  font-size:0.8rem;
  color:#bbbbbb;
}

/* ========== KPI COLUMN (RIGHT) ========== */
/* RIGHT KPI COLUMN — natural top alignment */
.kpi-column {
  display:flex;
  flex-direction:column;
  gap:8px;          /* space between KPI cards */
  padding-top:0;    /* ensure no top padding */
  margin-top:0;
}

/* Keep card spacing uniform */
.kpi-column .dt-kpi-card {
  margin-bottom:0;
}

</style>
""", unsafe_allow_html=True)


# =======================
# CONSTANTS & FIXED DATA
# =======================
DATA = pd.read_csv("./data_constants.csv", index_col=0)

# System definition and datasets used in this prototype.
ELECTROLYZER_KW = DATA.loc["el_rated_power_kw", "value"]                      # Electrolyser rated power
SEC = DATA.loc["sec_kwh_per_kg", "value"]                                  # Specific energy consumption (kWh per kg H₂)
LHV_H2 = DATA.loc["lhv_h2_kwh_per_kg", "value"]                              # Lower heating value of hydrogen (kWh/kg)
EMISSION_FACTOR_GRID = DATA.loc["em_factor_grid_kg_per_kwh", "value"]              # Dutch grid CO₂ intensity (kg CO₂/kWh)


# Installed capacities and annual demand used by the model.
pv_capacity_kw = DATA.loc["pv_capacity_kw", "value"]
wind_capacity_kw = DATA.loc["wind_capacity_kw", "value"]
electrolyzer_eff_kwh_per_kg = 48      # Conversion used for monthly H₂ charts
annual_h2_demand = DATA.loc["annual_h2_demand_kg", "value"] # kg/year (from facilities dataset)

enable_battery = True  # keep battery logic ON

BASE_CAP_KWH = DATA.loc["battery_cap_baseline_kwh", "value"]

bat_cap_kwh = BASE_CAP_KWH

ETA_CHG = DATA.loc["battery_eta_charge", "value"]
ETA_DIS = DATA.loc["battery_eta_discharge", "value"]

# =======================
# MAP DATA LOADING
# =====================

MAPBOX_KEY = 'pk.eyJ1IjoiY3lnbnVzMjYiLCJhIjoiY2s5Z2MzeWVvMGx3NTNtbzRnbGtsOXl6biJ9.8SLdJuFQzuN-s4OlHbwzLg'
STUDIO_STYLE ='mapbox://styles/cygnus26/clsei2b92016j01qqfc143six'
NODES_GEOJSON="../map/data/nodes.geojson"  # Placeholder path for map data
map_viewState = pdk.ViewState(
    latitude=52.374,
    longitude=6.642,
    zoom=14.5,
    pitch=60,
    bearing=-20
)



# Monthly capacity factors (CF) used to scale generation per calendar hour.
solar_cf = np.array([0.0425, 0.0752, 0.1210, 0.1656, 0.1701, 0.1755,
                     0.1672, 0.1544, 0.1337, 0.0896, 0.0539, 0.0364])
wind_cf  = np.array([0.3127, 0.3007, 0.1936, 0.2449, 0.1145, 0.1460,
                     0.1453, 0.1392, 0.1760, 0.1580, 0.1969, 0.2682])

# Monthly distribution of annual hydrogen demand (fractions that sum to 1).
demand_share_arr = np.array([0.1969, 0.1615, 0.1240, 0.0955, 0.0389, 0.0135,
                             0.0140, 0.0130, 0.0186, 0.0506, 0.1070, 0.1667])




# =======================
# SIDEBAR — SCENARIO CONTROLS
# =======================

with st.sidebar:
    st.image(
        "https://is2h4c-project.eu/wp-content/uploads/2024/03/Logo-Yifei.png",
        width=130,
    )

    # Smaller title + no extra spacing text
    st.markdown("### DT Dashboard Prototype")

    # -------- Energy source --------
    st.markdown("**Energy source feeding the electrolyser**")
    energy_source = st.radio(
        label="Energy source",
        options=[
            "Wind Only",
            "Solar Only",
            "Energy Mix (Solar + Wind)",
            "Grid Only",
        ],
        index=0,
    )

    st.markdown("---")

    # -------- Electrolyser schedule --------
    st.markdown("**Electrolyser operating hours**")
    hours_scenario = st.radio(
        label="Electrolizer operating hours",
        options=[
            "Baseline: 8 h/day on weekdays",
            "Custom",
        ],
        index=0,
    )

    if hours_scenario == "Custom":
        op_hours = st.slider(
            "Hours per weekday",
            min_value=1,
            max_value=24,
            value=8,
            step=1,
        )
    else:
        op_hours = 8

    op_hours_val = op_hours

    st.markdown("---")

    # (Optional short note instead of huge expander)
    st.caption(
        "Battery buffer is currently fixed to the baseline design "
        "(1.4 MWh, 95% charge/discharge)."
    )

# =======================
# TIME BASES FOR CALCULATION
# =======================
# 1) Calendar hours per month (for renewable generation — RE runs regardless of EL schedule).
days_in_month = np.array([calendar.monthrange(2025, m)[1] for m in range(1, 13)])
hours_in_month_calendar = days_in_month * 24

# 2) Weekday-only hours per month (for electrolyser schedule — reflects Mon–Fri operation).
hours_per_month_weekdays = np.array([
    len(pd.bdate_range(f"2025-{m:02d}-01", f"2025-{m:02d}-{days_in_month[m-1]}")) * op_hours_val
    for m in range(1, 13)
])

# =======================
# MONTHLY ENERGY AVAILABLE (DECOUPLED)
# =======================
# Renewable electricity is computed over calendar hours (correct physics).
monthly_solar_kwh_raw = pv_capacity_kw * solar_cf * hours_in_month_calendar
monthly_wind_kwh_raw  = wind_capacity_kw * wind_cf  * hours_in_month_calendar
monthly_res_kwh_raw   = monthly_solar_kwh_raw + monthly_wind_kwh_raw

# Electrolyser monthly setpoint (maximum electricity it can actually take) uses weekday-only hours.
max_monthly_kwh = ELECTROLYZER_KW * hours_per_month_weekdays

# =======================
# APPLY ENERGY SUPPLY CHOICE (with storage on renewables; Grid Only bypasses)
# =======================
# Choose renewable stream
if energy_source == "Wind Only":
    monthly_res_kwh = monthly_wind_kwh_raw
elif energy_source == "Solar Only":
    monthly_res_kwh = monthly_solar_kwh_raw
elif energy_source in ["Solar + Wind (Baseline)", "Energy Mix (Solar + Wind)"]:
    monthly_res_kwh = monthly_res_kwh_raw
else:  # "Grid Only"
    monthly_res_kwh = np.zeros(12)

# Outputs
usable_kwh        = np.zeros(12)  # electricity that reaches the EL
monthly_grid_kwh  = np.zeros(12)  # grid used (kept 0 unless Grid Only)
storage_soc_kwh   = np.zeros(12)  # battery end-of-month state of charge
charged_kwh       = np.zeros(12)  # gross energy sent into storage (before losses)
discharged_kwh    = np.zeros(12)  # energy delivered from storage to EL (after losses)
curtailed_kwh     = np.zeros(12)  # surplus renewables we couldn't store

# Grid Only is a clean counterfactual: storage is bypassed and EL runs at setpoint
if energy_source == "Grid Only":
    usable_kwh = max_monthly_kwh.copy()
    monthly_grid_kwh = max_monthly_kwh.copy()
    storage_soc_kwh[:] = 0
    charged_kwh[:] = 0
    discharged_kwh[:] = 0
    curtailed_kwh[:] = 0
else:
    # Battery bucket model (monthly)
    soc = 0.0  # start at empty; carries through months
    for m in range(12):
        cap_m = max_monthly_kwh[m]
        res_m = monthly_res_kwh[m]

        # 1) Direct feed from renewables up to EL cap
        direct = min(res_m, cap_m)
        usable = direct

        # 2) Store any remaining renewables (if battery enabled)
        surplus = max(0.0, res_m - direct)
        if enable_battery and bat_cap_kwh > 0:
            room = bat_cap_kwh - soc
            if room > 0:
                charge_in = min(surplus, room / ETA_CHG)  # input before charge loss
                soc += charge_in * ETA_CHG
                charged_kwh[m] = charge_in
                curtailed_kwh[m] = surplus - charge_in
            else:
                curtailed_kwh[m] = surplus
        else:
            curtailed_kwh[m] = surplus

        # 3) Discharge to cover remaining EL cap
        deficit = max(0.0, cap_m - usable)
        if enable_battery and soc > 0 and deficit > 0:
            deliverable = soc * ETA_DIS
            discharge = min(deficit, deliverable)
            if discharge > 0:
                soc -= discharge / ETA_DIS
                usable += discharge
                discharged_kwh[m] = discharge

        # 4) Record month
        storage_soc_kwh[m] = soc
        usable_kwh[m] = usable


# =======================
# H₂ PRODUCTION, DEMAND & BALANCE
# =======================
# Converts usable electricity to hydrogen; compares it to the monthly share of annual demand.
monthly_h2_production = usable_kwh / electrolyzer_eff_kwh_per_kg
monthly_h2_demand = demand_share_arr * annual_h2_demand
monthly_balance = monthly_h2_production - monthly_h2_demand

# KPI 4: % of annual hydrogen demand that is met by production across the year.
seasonal_coverage_pct = (monthly_h2_production.sum() / annual_h2_demand) * 100

# Data used by the charts in Column 3.
df_seasonal = pd.DataFrame({
    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "H₂ Production (kg)": monthly_h2_production,
    "H₂ Demand (kg)": monthly_h2_demand,
    "H₂ Balance (kg)": monthly_balance
})

# --- Waste heat recovery ---
HEAT_RECOVERY_FRAC = DATA.loc["heat_recovery_frac", "value"]  # 20% recoverable (Kumar et al., 2025; Lungu et al., 2025)
monthly_waste_heat_kWh = usable_kwh * HEAT_RECOVERY_FRAC
annual_waste_heat_kWh = monthly_waste_heat_kWh.sum()

# =======================
# KPI INPUTS (ANNUAL AGGREGATES)
# =======================
# These drive the KPI cards and the “Heat Source Breakdown” chart on the left.
annual_total_kwh_to_el = usable_kwh.sum()
annual_grid_kwh_to_el  = monthly_grid_kwh.sum()
annual_res_kwh_to_el   = annual_total_kwh_to_el - annual_grid_kwh_to_el

# Battery summary (for subtitles/readouts)
battery_throughput_kwh = discharged_kwh.sum() + (charged_kwh.sum() * ETA_CHG)  # delivered + stored energy (accounting once)
curtailed_total_kwh = curtailed_kwh.sum()
soc_min_kwh = float(storage_soc_kwh.min()) if storage_soc_kwh.size else 0.0
soc_max_kwh = float(storage_soc_kwh.max()) if storage_soc_kwh.size else 0.0
approx_cycles = (charged_kwh.sum() * ETA_CHG) / max(bat_cap_kwh, 1) if enable_battery and bat_cap_kwh > 0 else 0


hydrogen_kg_year    = annual_total_kwh_to_el / SEC                 # KPI 1: total hydrogen produced
green_h2_kg         = annual_res_kwh_to_el / SEC                   # Portion of H₂ made from renewables
heat_green_kWh      = green_h2_kg * LHV_H2                         # Renewable heat potential from green H₂
co2_avoided_kg      = heat_green_kWh * EMISSION_FACTOR_GRID        # KPI 2: avoided CO₂ (vs. grid heat)
heat_total_kWh      = hydrogen_kg_year * LHV_H2
non_green_heat_kWh  = heat_total_kWh - heat_green_kWh              # Heat attributable to grid input

# CO₂ emitted from grid electricity actually used by the EL (kWh → kg)
grid_emitted_co2_kg = annual_grid_kwh_to_el * EMISSION_FACTOR_GRID


# =======================
# MAP DATA LOADING
# =====================

def load_map_data():
    # --- Load node locations ---
    gdf_nodes = gpd.GeoDataFrame.from_file(NODES_GEOJSON)
    gdf_nodes["lon"] = gdf_nodes.geometry.x
    gdf_nodes["lat"] = gdf_nodes.geometry.y

    # --- Load flow data and attach coordinates ---
    df_flows = pd.read_csv("../map/data/flows.csv")

    for c in ("from_id", "to_id", "flow_type"):  # remove the crematoria flow (for now)
        df_flows[c] = df_flows[c].astype(str).str.strip()

    mask = df_flows["from_id"].eq("ELEC-01") & df_flows["to_id"].eq("CREM-01")
    df_flows = df_flows[~mask]

    src = gdf_nodes.rename(columns={"id": "from_id", "lon": "from_lon", "lat": "from_lat"})[
        ["from_id", "from_lon", "from_lat"]
    ]
    dst = gdf_nodes.rename(columns={"id": "to_id", "lon": "to_lon", "lat": "to_lat"})[
        ["to_id", "to_lon", "to_lat"]
    ]
    df_flows = df_flows.merge(src, on="from_id", how="left").merge(dst, on="to_id", how="left")


    # --- Assign colors by flow type ---
    COLOR_BY_TYPE = {
        "H2": [8, 104, 172],
        "O2": [102, 187, 106],
        "H2O": [38, 166, 154],
        "Waste Heat": [251, 140, 0],
        "Electricity": [142, 36, 170],
    }
    df_flows["color"] = df_flows["flow_type"].map(COLOR_BY_TYPE)

    # Build a concise tooltip per flow (adjust fields if your CSV differs)
    df_flows["tooltip"] = (
            df_flows["flow_type"].astype(str) + ": " +
            df_flows["from_id"].astype(str) + " → " + df_flows["to_id"].astype(str) +
            np.where(df_flows.get("value").notna(), " | " + df_flows["value"].astype(str), "") +
            np.where(df_flows.get("unit").notna(), " " + df_flows["unit"].astype(str), "")
    )

    # --- Create LineString geometry for each edge ---
    gdf_edges = gpd.GeoDataFrame(
        df_flows,
        geometry=df_flows.apply(
            lambda r: LineString([(r["from_lon"], r["from_lat"]), (r["to_lon"], r["to_lat"])]),
            axis=1,
        ),
        crs="EPSG:4326",
    )
    
    gdf_edges["value"] = gdf_edges["value"].apply(lambda x : random.randint(1,10))

    return gdf_nodes, gdf_edges


# =======================
# LAYOUT: KPIs, MAP, CHARTS
# =======================
# =======================
# LAYOUT: MAP + KPI RING (NEW SKELETON)
# =======================

# Some aggregate values for the new KPI cards
total_res_yield_kwh = float(monthly_res_kwh.sum())          # total renewable electricity available
total_el_input_kwh  = float(annual_total_kwh_to_el)         # electricity that actually reached EL
total_h2_kg         = float(hydrogen_kg_year)               # already computed above
total_co2_avoided   = float(co2_avoided_kg)
total_co2_grid      = float(grid_emitted_co2_kg)
total_waste_heat    = float(annual_waste_heat_kWh)

# Placeholders for KPIs not implemented yet (to be wired later)
battery_util_pct    = "—"
h2_storage_util_pct = "—"
o2_reuse_kg         = "—"
o2_reuse_pct        = "—"
co2_avoided_per_house = "—"

# Main layout: big map + vertical KPI column

main_col, right_col = st.columns([6, 2], gap="small", vertical_alignment="top")

# ===== MAIN COLUMN: MAP + BOTTOM KPI ROW =====
with main_col:
    # --- MAP COMPONENT (center, enlarged) ---
   
    with st.container(height="stretch"):
        with open("../map/map_test.html", 'r', encoding="utf-8") as f:
            mapbox_html = f.read()
        with open("../map/data/elec_to_houses.geojson", "r", encoding="utf-8") as f:
            pipe = json.load(f)
        nodes, edges = load_map_data()

        nodes_json = nodes.to_json()
        edges_json = edges.to_json()

        # Attach model outputs to pipeline feature collection
        h2_total = total_h2_kg

        def ensure_fc(g):
            if g.get("type") == "FeatureCollection":
                return g
            if g.get("type") in ("Feature", "LineString", "MultiLineString"):
                feat = g if g["type"] == "Feature" else {"type": "Feature", "properties": {}, "geometry": g}
                return {"type": "FeatureCollection", "features": [feat]}
            return {"type": "FeatureCollection", "features": []}

        fc = ensure_fc(pipe)
        for feat in fc.get("features", []):
            props = feat.setdefault("properties", {})
            props["value"] = float(h2_total)
            props["unit"] = "kg/yr"
            props["tooltip"] = f"H₂ to houses | {h2_total:,.0f} kg/yr"

        pipeline_json = json.dumps(fc)

        mapbox_html = mapbox_html.replace("__NODES__", nodes_json)
        mapbox_html = mapbox_html.replace("__EDGES__", edges_json)
        mapbox_html = mapbox_html.replace("__PIPELINE__", pipeline_json)
        mapbox_html = mapbox_html.replace("__ENERGY_SOURCE__", str(energy_source))

        components.html(mapbox_html, height="stretch", scrolling=False)

    st.markdown("")  # small spacer

    # --- BOTTOM ROW: 5 KPI CARDS (SECONDARY) ---
    bottom_cols = st.columns(5, gap="small")

    # 1. Renewable Electricity Yield
    with bottom_cols[0]:
        st.markdown(
            f"""
            <div class="dt-kpi-card">
              <h6>Renewable Electricity Yield</h6>
              <p>{annual_res_kwh_to_el:,.0f}</p>
              <span>kWh/yr (available RES)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Recoverable Waste Heat
    with bottom_cols[1]:
        st.markdown(
            f"""
            <div class="dt-kpi-card">
              <h6>Recoverable Waste Heat</h6>
              <p>{annual_waste_heat_kWh:,.0f}</p>
              <span>kWh/yr (20% of EL input)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. O₂ Reused (WWTP)
    with bottom_cols[2]:

        try:
            o2_reuse_kg = float(o2_reuse_kg)
        except:
            o2_reuse_kg = 0.0

        try:
            o2_reuse_pct = float(o2_reuse_pct)
        except:
            o2_reuse_pct = 0.0

        st.markdown(
            f"""
            <div class="dt-kpi-card">
              <h6>O₂ Reused (WWTP)</h6>
              <p>{o2_reuse_kg:,.0f}</p>
              <span>kg/yr – {o2_reuse_pct}% of demand </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. CO₂ Emissions Avoided (total)
    with bottom_cols[3]:
        st.markdown(
            f"""
            <div class="dt-kpi-card">
              <h6>CO₂ Emissions Avoided</h6>
              <p>{co2_avoided_kg:,.0f}</p>
              <span>kg CO₂/yr</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5. CO₂ Avoided per House
    with bottom_cols[4]:
        st.markdown(
            f"""
            <div class="dt-kpi-card">
              <h6>CO₂ Avoided per House</h6>
              <p>—</p>
              <span>kg CO₂/house·yr </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

   

# ===== RIGHT COLUMN: 5 PRIORITY KPI CARDS (VERTICAL STACK) =====
with right_col:
    # st.markdown("### ")

    # 1. Hydrogen Production
    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>Hydrogen Production</h6>
          <p>{hydrogen_kg_year:,.0f}</p>
          <span>kg H₂/yr</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Seasonal Coverage
    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>Seasonal Coverage</h6>
          <p>{seasonal_coverage_pct:,.0f}%</p>
          <span>of annual H₂ demand met</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Battery Buffer Utilisation (placeholder for now)
    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>Battery Utilisation</h6>
          <p>—</p>
          <span>% of capacity </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. H₂ Storage Utilisation (placeholder)
    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>H₂ Storage Utilisation</h6>
          <p>—</p>
          <span>% of 60 kg storage </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 5. CO₂ Emissions (Grid)
    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>CO₂ Emissions (Grid)</h6>
          <p>{grid_emitted_co2_kg:,.0f}</p>
          <span>kg CO₂/yr from grid input</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


