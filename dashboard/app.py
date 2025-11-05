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
# Unified dark styling for the entire app + reusable tooltip style for KPI help icons.
st.markdown("""
<style>
  [data-testid="AppViewContainer"], [data-testid="stAppViewContainer"] { background-color:#0e1117; color:#fafafa; }
  [data-testid="stSidebar"] { background-color:#40444d; }
  .dashboard-box h4, .dashboard-box li, .dashboard-box p { color:#ffffff !important; }
  [data-testid="stSidebar"], [data-testid="stSidebar"] * { color:#ffffff !important; }

  .tooltip { position:relative; display:inline-block; cursor:pointer; }
  .tooltiptext {
    visibility:hidden; width:260px; background:#333; color:#fff; text-align:left; border-radius:6px; padding:10px;
    position:absolute; z-index:1; top:100%; left:50%; transform:translateX(-50%);
    opacity:0; transition:opacity .3s; font-size:13px; box-shadow:0 0 10px rgba(0,0,0,.5);
  }
  .tooltip:hover .tooltiptext { visibility:visible; opacity:1; }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="stDecoration"] { display: none; }

header[data-testid="stHeader"] { background: transparent; }

[data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)


# =======================
# CONSTANTS & FIXED DATA
# =======================
# System definition and datasets used in this prototype.
ELECTROLYZER_KW = 70                      # Electrolyser rated power
SEC = 48                                  # Specific energy consumption (kWh per kg H₂)
LHV_H2 = 33.3                             # Lower heating value of hydrogen (kWh/kg)
EMISSION_FACTOR_GRID = 0.388              # Dutch grid CO₂ intensity (kg CO₂/kWh)


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

# Installed capacities and annual demand used by the model.
pv_capacity_kw = 1080
wind_capacity_kw = 100
electrolyzer_eff_kwh_per_kg = 48      # Conversion used for monthly H₂ charts
annual_h2_demand = 4922                   # kg/year (from facilities dataset)

# =======================
# SIDEBAR — SCENARIO CONTROLS
# =======================
with st.sidebar:
    st.image("https://is2h4c-project.eu/wp-content/uploads/2024/03/Logo-Yifei.png", width=250)
    st.title("DT Dashboard Prototype")

    # Energy supply selection: for realism, "Solar + Wind (Baseline)" feeds both sources together.
    st.markdown("### Select an energy source feeding the electrolyser")
    energy_source = st.radio("", ("Wind Only", "Solar Only", "Energy Mix (Solar + Wind)", "Grid Only"))

    # Operating hours define the electrolyser schedule. Baseline: 8 hours per weekday (Mon–Fri).
    st.markdown("---")
    st.markdown("### Electrolyser operational hours")
    hours_scenario = st.radio("", ("Baseline: 8 h/day on weekdays", "Custom"))
    if hours_scenario == "Custom":
        op_hours = st.slider("Operating hours per weekday", min_value=1, max_value=24, value=8, step=1)
        # Apply selected hours (Baseline = 8 h/weekday)

    op_hours_val = op_hours if (hours_scenario == "Custom") else 8

    st.markdown("---")

    # --- Storage (renewables buffer) ---
    with st.expander("Storage (renewables buffer)", expanded=True):
        enable_battery = st.checkbox(
            "Enable battery (LFP)", value=True,
            help="Battery stores surplus solar/wind and releases it during EL hours."
        )

        # Baseline spec (Danny)
        BASE_CAP_KWH = 1400
        BASE_ETA_PCT = 95  # both charge and discharge

        # One-time init so custom values persist when Baseline is toggled off/on
        if "bat_settings_initialized" not in st.session_state:
            st.session_state.bat_cap_kwh = BASE_CAP_KWH
            st.session_state.eta_chg_pct = BASE_ETA_PCT
            st.session_state.eta_dis_pct = BASE_ETA_PCT
            st.session_state.bat_settings_initialized = True

        use_baseline_battery = st.checkbox(
            "Baseline", value=True,
            help="Sets 1.4 MWh capacity and 95% charge/discharge efficiencies."
        )

        if use_baseline_battery:
            # Auto-apply & lock UI
            bat_cap_kwh = BASE_CAP_KWH
            eta_chg_pct = BASE_ETA_PCT
            eta_dis_pct = BASE_ETA_PCT

            st.number_input("Battery capacity (kWh)", min_value=0, value=bat_cap_kwh, step=100, disabled=True)
            st.slider("Charge efficiency (%)", 70, 100, eta_chg_pct, disabled=True)
            st.slider("Discharge efficiency (%)", 70, 100, eta_dis_pct, disabled=True)

        else:
            # Editable; persist user choices
            bat_cap_kwh = st.number_input(
                "Battery capacity (kWh)", min_value=0,
                value=int(st.session_state.bat_cap_kwh), step=50,
                help="If not using baseline, enter your own capacity."
            )
            eta_chg_pct = st.slider(
                "Charge efficiency (%)", 70, 100,
                int(st.session_state.eta_chg_pct)
            )
            eta_dis_pct = st.slider(
                "Discharge efficiency (%)", 70, 100,
                int(st.session_state.eta_dis_pct)
            )

            # Save to session so it sticks if the user toggles baseline later
            st.session_state.bat_cap_kwh = bat_cap_kwh
            st.session_state.eta_chg_pct = eta_chg_pct
            st.session_state.eta_dis_pct = eta_dis_pct

    # Effective efficiencies for the dispatch logic
    ETA_CHG = eta_chg_pct / 100.0
    ETA_DIS = eta_dis_pct / 100.0

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
HEAT_RECOVERY_FRAC = 0.20  # 20% recoverable (Kumar et al., 2025; Lungu et al., 2025)
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
col1, col2, col3 = st.columns([1.2, 2.6, 1.4], gap="small")

# ===== LEFT COLUMN: KPI CARDS =====
with col1:
    # KPI 1 — Annual hydrogen production
    kpi_row1 = st.columns(2, gap="small")
    with kpi_row1[0]:
        st.markdown(f"""
            <div style='background:#26264d; padding:20px 15px 10px 15px; border-radius:10px; margin-bottom:10px;'>
                <h6 style='color:#A3A6F7; display:flex; align-items:center; gap:6px;'>
                  Hydrogen Production
                  <span class="tooltip">&#9432;
                    <span class="tooltiptext">
                      Total annual hydrogen produced from all electricity that reached the electrolyser
                      (renewables first, plus grid if selected).
                      <br><br>
                      • Electrolyser: 70 kW<br>
                      • Operating hours: weekdays only (sidebar)<br>
                      • SEC: 48 kWh per kg H₂
                    </span>
                  </span>
                </h6>
                <p style='font-size:1.8rem; color:white; margin:0; font-weight:bold;'>{hydrogen_kg_year:,.0f}</p>
                <span style='font-size:1rem; color:#bbb;'>kg/year</span>
            </div>
        """, unsafe_allow_html=True)

    # KPI 2 — Dynamic: Emissions (Grid Only) or Avoided (Renewables)
    with kpi_row1[1]:
        is_grid_only = (energy_source == "Grid Only")
        kpi2_title = "CO₂ Emissions (Grid)" if is_grid_only else "CO₂ Emissions Avoided"
        kpi2_value = grid_emitted_co2_kg if is_grid_only else co2_avoided_kg
        kpi2_unit = "kg/year"

        # Tooltips tailored to the active mode
        if is_grid_only:
            kpi2_help = (
                "Total CO₂ emitted from running the electrolyser on grid electricity only.\n\n"
                "Calculated as: (EL setpoint kWh from grid) × (grid CO₂ intensity)."
            )
        else:
            kpi2_help = (
                "Emissions avoided by using the renewable portion of electricity instead of the Dutch grid.\n\n"
                "Calculated as: (heat from green H₂) × (grid CO₂ intensity). Grid input does not contribute to avoided CO₂."
            )

        st.markdown(f"""
            <div style='background:#26264d; padding:20px 15px 10px 15px; border-radius:10px; margin-bottom:10px;'>
                <h6 style='color:#A3A6F7; display:flex; align-items:center; gap:6px;'>
                  {kpi2_title}
                  <span class="tooltip">&#9432;
                    <span class="tooltiptext">{kpi2_help}</span>
                  </span>
                </h6>
                <p style='font-size:1.8rem; color:white; margin:0; font-weight:bold;'>{kpi2_value:,.0f}</p>
                <span style='font-size:1rem; color:#bbb;'>{kpi2_unit}</span>
            </div>
        """, unsafe_allow_html=True)

    # KPI 3 — Heat from Green H₂ and coverage illustration
    kpi_row2 = st.columns(2, gap="small")
    with kpi_row2[0]:
        # Example translation from green H₂ to building heat intensity (communication KPI)
        house_areas = [230, 229, 478, 597]
        total_area_m2 = sum(house_areas)
        boiler_efficiency = 0.95
        demand_A = 75 / boiler_efficiency  # A-rated benchmark, adjusted for boiler efficiency

        heat_per_m2_green = heat_green_kWh / total_area_m2 if total_area_m2 > 0 else 0
        coverage_A = (heat_per_m2_green / demand_A) * 100 if demand_A > 0 else 0

        tooltip_text = f"""
        Green heat intensity illustration (communication metric):<br>
        {''.join([f'House {i} ({area} m²): {heat_per_m2_green:,.1f} kWh/m²/yr<br>' for i, area in enumerate(house_areas, start=1)])}
        ≈ {coverage_A:,.0f}% of an A-rated house demand (assumes 95% boiler efficiency).
        """

        st.markdown(f"""
            <div style='background:#26264d; padding:20px 15px 10px 15px; border-radius:10px; margin-bottom:10px;'>
                <h6 style='color:#A3A6F7; display:flex; align-items:center; gap:6px;'>
                  Heat from Green H₂
                  <span class="tooltip">&#9432;<span class="tooltiptext">{tooltip_text}</span></span>
                </h6>
                <p style='font-size:1.8rem; color:white; margin:0; font-weight:bold;'>{heat_green_kWh:,.0f}</p>
                <span style='font-size:1rem; color:#bbb;'>kWh/year</span>
            </div>
        """, unsafe_allow_html=True)

    # KPI 4 — Seasonal coverage (% of demand met)
    with kpi_row2[1]:
        st.markdown(f"""
            <div style='background:#26264d; padding:20px 15px 10px 15px; border-radius:10px; margin-bottom:10px;'>
                <h6 style='color:#A3A6F7; display:flex; align-items:center; gap:6px;'>
                  Seasonal Coverage
                  <span class="tooltip">&#9432;
                    <span class="tooltiptext">
                      Share of annual hydrogen demand that is met by monthly production.
                      Electrolyser hours limit monthly intake; renewables vary by season.
                    </span>
                  </span>
                </h6>
                <p style='font-size:1.8rem; color:white; margin:0; font-weight:bold;'>{seasonal_coverage_pct:,.0f}%</p>
                <p style='font-size:1rem; color:#bbb; margin:0;'>of annual H₂ demand</p>
            </div>
        """, unsafe_allow_html=True)

    # CO₂ emitted from grid electricity actually used by the EL (kWh → kg)
    grid_emitted_co2_kg = annual_grid_kwh_to_el * EMISSION_FACTOR_GRID

    # Battery Utilization mini-chart (fixed month order)
    st.markdown("<h6 style='color:#A3A6F7; margin-top:16px;'>Battery Utilization (SOC over the year)</h6>",
                unsafe_allow_html=True)

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    df_batt = pd.DataFrame({
        "Month": month_order,
        "SOC (kWh)": storage_soc_kwh,
        "Curtailed RES (kWh)": curtailed_kwh,
        "Charged (kWh)": charged_kwh * ETA_CHG,  # net energy stored
        "Discharged (kWh)": discharged_kwh  # energy delivered to EL
    })

    soc_chart = (
        alt.Chart(df_batt)
        .mark_area(opacity=0.5)
        .encode(
            x=alt.X("Month:N", sort=month_order, axis=alt.Axis(labelColor="white", title=None)),
            y=alt.Y("SOC (kWh):Q", axis=alt.Axis(labelColor="white", title="State of Charge (kWh)")),
            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip("SOC (kWh):Q", format=",.0f"),
                alt.Tooltip("Charged (kWh):Q", format=",.0f", title="Stored this month"),
                alt.Tooltip("Discharged (kWh):Q", format=",.0f", title="Delivered this month"),
                alt.Tooltip("Curtailed RES (kWh):Q", format=",.0f")
            ]
        )
        .properties(width=550, height=230, background="#1E1E2F")
        .configure_view(stroke=None)
    )

    st.altair_chart(soc_chart, use_container_width=True)

    # Small readout for supervisors
    st.caption(
        f"Peak SOC: {soc_max_kwh:,.0f} kWh | Min SOC: {soc_min_kwh:,.0f} kWh | "
        f"Curtailed RES: {curtailed_total_kwh:,.0f} kWh | Approx. cycles: {approx_cycles:,.1f}"
    )

    # Monthly Waste Heat Recovery chart
    st.markdown("<h6 style='color:#A3A6F7; margin-top:16px;'>Monthly Waste Heat Recovery</h6>", unsafe_allow_html=True)

    df_waste = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Recovered Heat (kWh)": monthly_waste_heat_kWh
    })

    whr_chart = (
        alt.Chart(df_waste)
        .mark_bar(color="#FFB347")  # orange-golden bars for heat
        .encode(
            x=alt.X("Month:N",
                    sort=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                    axis=alt.Axis(labelColor="white")),
            y=alt.Y("Recovered Heat (kWh):Q", axis=alt.Axis(labelColor="white", title="kWh")),
            tooltip=[alt.Tooltip("Month:N", title="Month"),
                     alt.Tooltip("Recovered Heat (kWh):Q", format=",.0f")]
        )
        .properties(width=500, height=250, background="#1E1E2F")
        .configure_view(stroke=None)
    )

    st.altair_chart(whr_chart, use_container_width=True)

    # Caption
    st.caption(f"Assumes 20% of electricity delivered to the EL is recoverable as low-temperature heat. "
               f"Annual total ≈ {annual_waste_heat_kWh:,.0f} kWh (literature: Van der Roest et al. 2023; IEEE 2023).")

# ===== CENTER COLUMN: MAP PLACEHOLDER =====
with col2:
    
    with open("../map/map_test.html", 'r', encoding="utf-8") as f:
        mapbox_html = f.read()
    with open("../map/data/elec_to_houses.geojson", "r", encoding="utf-8") as f:
        pipe = json.load(f)
    nodes , edges = load_map_data()
    print(edges) 

    nodes_json = nodes.to_json()
    edges_json = edges.to_json()

    # Pipeline value assigning
    h2_total = hydrogen_kg_year  # already computed in your app

    def ensure_fc(g):
        if g.get("type") == "FeatureCollection":
            return g
        # wrap a single feature/geometry as a FeatureCollection
        if g.get("type") in ("Feature", "LineString", "MultiLineString"):
            feat = g if g["type"] == "Feature" else {"type": "Feature", "properties": {}, "geometry": g}
            return {"type": "FeatureCollection", "features": [feat]}
        return {"type": "FeatureCollection", "features": []}

    fc = ensure_fc(pipe)

    for feat in fc.get("features", []):
        props = feat.setdefault("properties", {})
        # attach model-driven properties
        props["value"] = float(h2_total)  # numeric for width scaling
        props["unit"] = "kg/yr"
        props["tooltip"] = f"H₂ to houses | {h2_total:,.0f} kg/yr"

    pipeline_json = json.dumps(fc)


    mapbox_html = mapbox_html.replace("__NODES__", nodes_json)
    mapbox_html = mapbox_html.replace("__EDGES__", edges_json)
    mapbox_html = mapbox_html.replace("__PIPELINE__", pipeline_json)
    mapbox_html = mapbox_html.replace("__ENERGY_SOURCE__", str(energy_source))

    components.html(mapbox_html, height=900)



    # nodes, edges = load_map_data()

    # def load_layers():
    #     # Placeholder for map layers (e.g., facilities, infrastructure).
    #     layers = [
    #         pdk.Layer(
    #             "ScatterplotLayer",
    #             data=nodes,
    #             get_position=["lon", "lat"],
    #             get_color="[200, 30, 0, 160]",
    #             auto_highlight=True,
    #             get_radius=10,
    #             pickable=True,
                
    #         ),
    #         pdk.Layer(
    #             "ArcLayer",
    #             data=edges,
    #             get_source_position=["from_lon", "from_lat"],
    #             get_target_position=["to_lon", "to_lat"],
    #             get_source_color="color",
    #             get_target_color="color",
    #             pickable=True,
    #             auto_highlight=True,
    #             width_scale=5,
    #             width_min_pixels=2
    #         )
            
    #         # Add more layers as needed
            
    
            
    #     ]
    #     return layers
    
    # deck = pdk.Deck(layers=load_layers(), initial_view_state=map_viewState, 
    #                 tooltip={"text": "{name}"},
    #                 api_keys={"mapbox": 'pk.eyJ1IjoiaGlzaGFtYWZhc2giLCJhIjoiY21mM3NrcGRlMDAweTJrczNyZzJhdWNyNSJ9.E_YstJ3rUCf1TtkF7_jjoQ'},
    #                 map_provider="mapbox",
    #                 map_style="light",
    #                 )
    # map_card = st.pydeck_chart(deck, use_container_width=True)
    
    # st.markdown("""
    #     <div style="background-color:#2e2e2e; padding:20px; border-radius:8px; height:600px;
    #                 display:flex; align-items:center; justify-content:center;">
    #       <span style="color:#cccccc; font-size:18px;">Map Placeholder</span>
    #     </div>
    # """, unsafe_allow_html=True)

# ===== RIGHT COLUMN: CONTEXT CHARTS =====
with col3:
    # Line chart: monthly hydrogen production vs. demand (communicates seasonal match/mismatch).
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df_seasonal["Month"] = pd.Categorical(df_seasonal["Month"], categories=month_order, ordered=True)
    df_seasonal = df_seasonal.sort_values("Month")

    df_melted = df_seasonal.melt(
        id_vars=["Month"],
        value_vars=["H₂ Production (kg)", "H₂ Demand (kg)"],
        var_name="type",
        value_name="value"
    )
    df_melted["Month"] = pd.Categorical(df_melted["Month"], categories=month_order, ordered=True)

    line_chart = (
        alt.Chart(df_melted)
        .mark_line(point=alt.OverlayMarkDef(size=90))
        .encode(
            x=alt.X("Month:N", sort=None, title="Month",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            y=alt.Y("value:Q", title="Hydrogen (kg)",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(domain=["H₂ Production (kg)", "H₂ Demand (kg)"],
                                range=["#00BFFF", "#FFA07A"]),
                legend=alt.Legend(orient="bottom", direction="horizontal", title=None,
                                  labelColor="white", labelLimit=1000,
                                  symbolStrokeColor="white", symbolSize=220, padding=8)
            ),
            tooltip=[alt.Tooltip("Month:N", title="Month"),
                     alt.Tooltip("type:N", title="Series"),
                     alt.Tooltip("value:Q", title="H₂ (kg)", format=",.0f")]
        )
        .properties(width=550, height=400, background="#1E1E2F",
                    title=alt.TitleParams(text="Monthly Hydrogen Production vs Demand",
                                          color="white", fontSize=16, anchor="start"),
                    padding={"left":0,"right":0,"top":5,"bottom":5})
        .configure_view(stroke=None)
    )
    st.altair_chart(line_chart, use_container_width=False)

    # Storage view: monthly surplus/deficit bars with a state-of-charge line (no-loss abstraction).
    df_seasonal["H₂ Balance (kg)"] = df_seasonal["H₂ Production (kg)"] - df_seasonal["H₂ Demand (kg)"]
    df_seasonal["cum_net"] = df_seasonal["H₂ Balance (kg)"].cumsum()
    s_min, s_max = float(df_seasonal["cum_net"].min()), float(df_seasonal["cum_net"].max())
    required_capacity_kg = s_max - s_min         # Minimum seasonal storage to avoid curtailment/shortage
    initial_soc = -s_min                         # Shifts SOC to always stay ≥ 0 in the chart
    df_seasonal["SOC (kg)"] = df_seasonal["cum_net"] + initial_soc

    df_for_bars = df_seasonal.copy()
    df_for_bars["Category"] = np.where(df_for_bars["H₂ Balance (kg)"] >= 0, "Surplus", "Deficit")

    color_scale = alt.Scale(domain=["Surplus","Deficit","Storage Level"],
                            range=["#40E0D0","#FF6B6B","#FFD166"])

    bar_layer = (
        alt.Chart(df_for_bars).mark_bar().encode(
            x=alt.X("Month:N", sort=None, title="Month",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            y=alt.Y("H₂ Balance (kg):Q", title="Monthly Surplus / Deficit (kg)",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            color=alt.Color("Category:N", scale=color_scale, title=None,
                            legend=alt.Legend(orient="bottom", labelColor="white",
                                              symbolStrokeColor="white", symbolSize=220)),
            tooltip=[alt.Tooltip("Month:N", title="Month"),
                     alt.Tooltip("H₂ Balance (kg):Q", format=",.0f", title="Monthly Balance (kg)"),
                     alt.Tooltip("SOC (kg):Q", format=",.0f", title="SOC after Month (kg)")]
        )
    )

    soc_layer = (
        alt.Chart(df_seasonal)
        .transform_calculate(Category="'Storage Level'")
        .mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=2)
        .encode(
            x=alt.X("Month:N", sort=None),
            y=alt.Y("SOC (kg):Q", title="Storage Level (kg)",
                    axis=alt.Axis(labelColor="white", titleColor="white")),
            color=alt.Color("Category:N", scale=color_scale, title=None, legend=None)
        )
    )

    storage_chart = (
        alt.layer(bar_layer, soc_layer)
        .resolve_scale(y="independent")
        .properties(
            width=550, height=400, background="#1E1E2F",
            title=alt.TitleParams(
                text=["Hydrogen Storage Operation:", "Monthly Balance & State of Charge"],
                subtitle=f"Min. seasonal storage (no losses): {required_capacity_kg:,.0f} kg H₂",
                color="white", subtitleColor="white", fontSize=15, subtitleFontSize=12, anchor="start"
            ),
            padding={"left":0,"right":0,"top":5,"bottom":5}
        ).configure_view(stroke=None)
    )
    st.altair_chart(storage_chart, use_container_width=False)

    # ---- O₂ Reuse: Electricity Saved (Circularity Synergy) ----
    # Calculation: O₂ mass from H₂ production × reuse% × aeration SEC
    # (Defaults: 30% reuse, 0.5 kWh/kg O₂)
    o2_reuse_fraction = 0.30
    aeration_sec = 0.5   # kWh per kg O₂
    df_seasonal["O₂ mass (kg)"] = df_seasonal["H₂ Production (kg)"] * 8.0
    df_seasonal["O₂ Saved Elec (kWh)"] = (
        df_seasonal["O₂ mass (kg)"] * o2_reuse_fraction * aeration_sec
    )

    o2_saved_total = df_seasonal["O₂ Saved Elec (kWh)"].sum()

    # KPI card above chart
    st.markdown(
        f"""
        <div style="background-color:#1E1E2F; padding:5px; border-radius:10px; 
                    text-align:left; color:white; font-size:15px;">
            <b>O₂ Reuse – Electricity Saved</b><br>
            {o2_saved_total:,.0f} kWh/yr
        </div>
        """,
        unsafe_allow_html=True
    )

    # Monthly bar chart for O₂ reuse
    o2_chart = (
        alt.Chart(df_seasonal)
        .mark_bar()
        .encode(
            x=alt.X("Month:N", sort=None, title="Month",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            y=alt.Y("O₂ Saved Elec (kWh):Q", title="Electricity Saved (kWh)",
                    axis=alt.Axis(labelColor="white", titleColor="white", labelLimit=1000)),
            tooltip=[
                alt.Tooltip("Month:N", title="Month"),
                alt.Tooltip("O₂ mass (kg):Q", format=",.0f", title="O₂ Produced (kg)"),
                alt.Tooltip("O₂ Saved Elec (kWh):Q", format=",.0f", title="Elec Saved (kWh)")
            ],
            color=alt.value("#32CD32")
        )
        .properties(
            width=550, height=300, background="#1E1E2F",
            title=alt.TitleParams(
                text="Monthly Electricity Saved by O₂ Reuse",
                color="white", fontSize=16, anchor="start"
            ),
            padding={"left":0,"right":0,"top":5,"bottom":5}
        )
        .configure_view(stroke=None)
    )

    st.altair_chart(o2_chart, use_container_width=False)


    # Tabs for additional context (indicators, scenario details, documentation).
    tabs = st.tabs(["All Indicators", "Scenario Details", "About"])
    with tabs[0]:
        st.write("**Full Indicators Table** will go here.")
    with tabs[1]:
        st.write("**Scenario Parameters** are summarised here (Energy Source, Grid backup, Operating hours).")
        st.write({
            "Energy source": energy_source,
            "Hours per weekday": int(op_hours_val),
            "Total annual EL hours (weekdays only)": int(hours_per_month_weekdays.sum())
        })
    with tabs[2]:
        st.write("**About this prototype**")
        st.write(
            "- Pre-implementation assessment of the H₂Hub Twente concept.\n"
            "- Renewables are calculated on calendar hours (independent of EL schedule).\n"
            "- Electrolyser intake is capped by power and weekday-only operating hours.\n"
            "- Storage chart uses a no-loss seasonal abstraction to illustrate required storage volume."
        )


with st.expander("Diagnostics (energy flows)"):
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df_diag = pd.DataFrame({
        "Month": month_order,
        "RES avail (kWh)":      monthly_res_kwh,
        "EL cap (kWh)":         max_monthly_kwh,
        "Direct to EL (kWh)":   np.minimum(monthly_res_kwh, max_monthly_kwh),
        "Charge input (kWh)":   charged_kwh,                   # before charge loss
        "Discharged (kWh)":     discharged_kwh,               # delivered to EL (after loss)
        "Curtailed (kWh)":      curtailed_kwh,
        "SOC end (kWh)":        storage_soc_kwh,
        "Usable to EL (kWh)":   usable_kwh,
        "H2 prod (kg)":         usable_kwh / 52.5,
        "H2 demand (kg)":       monthly_h2_demand,
        "Balance (kg)":         (usable_kwh / 52.5) - monthly_h2_demand
    })
    # Simple assertions (printed as text so you can see if any fail)
    eps = 1e-6
    res_balance_ok = np.allclose(
        df_diag["RES avail (kWh)"].values,
        df_diag["Direct to EL (kWh)"].values + df_diag["Charge input (kWh)"].values + df_diag["Curtailed (kWh)"].values,
        atol=1e-3
    )
    el_balance_ok = np.allclose(
        df_diag["Usable to EL (kWh)"].values,
        df_diag["Direct to EL (kWh)"].values + df_diag["Discharged (kWh)"].values,
        atol=1e-3
    )
    st.write(f"RES balance OK: {res_balance_ok} | EL balance OK: {el_balance_ok} | SOC within [0, cap]: {bool((storage_soc_kwh>=-eps).all() and (storage_soc_kwh<=bat_cap_kwh+eps).all())}")
    st.dataframe(df_diag.style.format({
        "RES avail (kWh)": "{:,.0f}",
        "EL cap (kWh)": "{:,.0f}",
        "Direct to EL (kWh)": "{:,.0f}",
        "Charge input (kWh)": "{:,.0f}",
        "Discharged (kWh)": "{:,.0f}",
        "Curtailed (kWh)": "{:,.0f}",
        "SOC end (kWh)": "{:,.0f}",
        "Usable to EL (kWh)": "{:,.0f}",
        "H2 prod (kg)": "{:,.0f}",
        "H2 demand (kg)": "{:,.0f}",
        "Balance (kg)": "{:,.0f}",
    }), use_container_width=True)
