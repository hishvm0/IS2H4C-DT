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
# UI STATE
# =======================
if "show_battery_diag" not in st.session_state:
    st.session_state.show_battery_diag = False

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
/* ---------- TOOLTIP (generic, used in KPI headers) ---------- */
.tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid #888;
  font-size: 9px;
  line-height: 1;
  margin-left: 6px;
  cursor: help;
  z-index: 20;              /* sits above normal card content */
}

.tooltiptext {
  visibility: hidden;
  max-width: 360px;
  background:#333;
  color:#fff;
  text-align:left;
  border-radius:6px;
  padding:8px 10px;
  position:absolute;
  bottom:100%;              /* show ABOVE the icon */
  left:50%;
  transform:translateX(-50%);
  margin-bottom:6px;
  opacity:0;
  transition:opacity .2s;
  font-size:12px;
  line-height:1.3;
  white-space:normal;
  word-wrap:break-word;
  box-shadow:0 0 10px rgba(0,0,0,.5);
  z-index:9999;             /* make sure it beats the big number */
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}

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
  min-height:95px;
  display:flex;
  flex-direction:column;
  justify-content:center;
  margin-bottom:8px;

  position: relative;   /* NEW: so tooltip can sit above card */
  overflow: visible;    /* NEW: don't clip tooltip */
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
/* ==== Battery KPI: button visually inside the card ==== */
.battery-card {
  margin-bottom: 4px;  /* slightly smaller gap under this card */
}

.battery-button-wrap {
  margin-top: -4px;      /* pull button up towards the card */
  padding: 0 12px 4px;   /* align with card padding horizontally */
}

.battery-button-wrap button {
  width: 100%;
  font-size: 0.8rem;
  border-radius: 8px;
}
/* Fix for tooltips inside KPI cards */
.dt-kpi-card h6 {
  position: relative;
  overflow: visible !important;
}

.dt-kpi-card .tooltip {
  position: relative;
  display: inline-block;
}

.dt-kpi-card .tooltip .tooltiptext {
  visibility: hidden;
  opacity: 0;
  width: 240px;
  background: #333;
  color: #fff;
  border-radius: 6px;
  padding: 10px;
  position: absolute;
  z-index: 99999;                 
  bottom: -10px;
  left: 105%;
  transform: translateY(-50%);
  transition: opacity 0.2s;
  white-space: normal;
}

.dt-kpi-card .tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
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
PV_ALLOCATION_FACTOR = 0.30  # 30% of installed PV is effectively allocated to H₂ system
pv_capacity_effective_kw = pv_capacity_kw * PV_ALLOCATION_FACTOR
BASE_CAP_KWH = DATA.loc["battery_cap_baseline_kwh", "value"]

bat_cap_kwh = BASE_CAP_KWH

ETA_CHG = DATA.loc["battery_eta_charge", "value"]
ETA_DIS = DATA.loc["battery_eta_discharge", "value"]

EMISSION_FACTOR_NG = DATA.loc["em_factor_ng_kg_per_kwh", "value"]

BOILER_EFFICIENCY = DATA.loc["boiler_efficiency", "value"]
A_DEMAND_REF = DATA.loc["a_demand_ref_kwh_per_m2", "value"]
TOTAL_HEATED_AREA_M2 = DATA.loc["total_heated_area_m2", "value"]

HOUSE_AREAS = [
    DATA.loc["house1_area_m2", "value"],
    DATA.loc["house2_area_m2", "value"],
    DATA.loc["house3_area_m2", "value"],
    DATA.loc["house4_area_m2", "value"],
]

H2_STORAGE_CAPACITY_KG = DATA.loc["h2_storage_capacity_kg", "value"]
O2_PER_KG_H2 = DATA.loc["o2_per_kg_h2", "value"]
WWTP_O2_DEMAND = DATA.loc["wwtp_o2_demand_annual", "value"]

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
monthly_solar_kwh_raw = pv_capacity_effective_kw * solar_cf * hours_in_month_calendar
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
el_unserved_kwh     = np.zeros(12)  # EL cap that was not served by RES + battery

# Grid Only is a clean counterfactual: storage is bypassed and EL runs at setpoint
if energy_source == "Grid Only":
    usable_kwh = max_monthly_kwh.copy()
    monthly_grid_kwh = max_monthly_kwh.copy()
    storage_soc_kwh[:] = 0
    charged_kwh[:] = 0
    discharged_kwh[:] = 0
    curtailed_kwh[:] = 0
    el_unserved_kwh[:]     = 0

else:
    # Battery bucket model (monthly)
    soc = 0.0  # start at empty; carries through months
    for m in range(12):
        cap_m = max_monthly_kwh[m]      # EL monthly electricity cap
        res_m = monthly_res_kwh[m]      # renewable electricity available

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

        # 3b) Whatever wasn’t served even after battery = unserved EL demand
        el_unserved_kwh[m] = max(0.0, cap_m - usable)

        # 4) Record month
        storage_soc_kwh[m] = soc
        usable_kwh[m] = usable
# Count months where the battery actually discharged to EL
battery_months_active = int(np.sum(discharged_kwh > 0))


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

# =======================
# BATTERY DIAGNOSTICS TABLE (MONTHLY)
# =======================
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

df_battery_diag = pd.DataFrame({
    "Month": month_labels,
    "RES available (kWh)":      monthly_res_kwh,
    "EL cap (kWh)":             max_monthly_kwh,
    "EL input to electrolyser (kWh)": usable_kwh,
    "Battery charge input (kWh)":     charged_kwh,       # energy sent into battery (before losses)
    "Battery discharge to EL (kWh)":  discharged_kwh,    # energy delivered from battery to EL
    "RES remainder (kWh)": curtailed_kwh,
    "Battery SOC end of month (kWh)": storage_soc_kwh,
    "Unserved EL cap (kWh)":    el_unserved_kwh,
    "H₂ production (kg)":       monthly_h2_production,
    "H₂ demand (kg)":           monthly_h2_demand,
    "H₂ balance (kg)":          monthly_balance,
})
# battery summary for the KPI card
months_with_discharge = int((discharged_kwh > 0).sum())
months_with_unserved  = int((el_unserved_kwh > 1e-3).sum())
total_curtailed_mwh   = curtailed_total_kwh / 1000.0  # from kWh to MWh

# Simple diagnostics for the battery view
battery_months_active = int(np.count_nonzero(charged_kwh + discharged_kwh))
curtailed_res_MWh_year = curtailed_total_kwh / 1000.0


hydrogen_kg_year    = annual_total_kwh_to_el / SEC                 # KPI 1: total hydrogen produced
green_h2_kg         = annual_res_kwh_to_el / SEC                   # Portion of H₂ made from renewables
heat_green_kWh      = green_h2_kg * LHV_H2                         # Renewable heat potential from green H₂
co2_avoided_kg      = heat_green_kWh * EMISSION_FACTOR_GRID        # KPI 2: avoided CO₂ (vs. grid heat)
heat_total_kWh      = hydrogen_kg_year * LHV_H2
non_green_heat_kWh  = heat_total_kWh - heat_green_kWh              # Heat attributable to grid input

# CO₂ emitted from grid electricity actually used by the EL (kWh → kg)
grid_emitted_co2_kg = annual_grid_kwh_to_el * EMISSION_FACTOR_GRID

# =======================
# O₂ REUSE KPI (WWTP COVERAGE)
# =======================
# Total O₂ produced from H₂ electrolysis
total_o2_from_h2_kg = hydrogen_kg_year * O2_PER_KG_H2

# For now, assume all produced O₂ can be reused up to WWTP demand
o2_reuse_kg = min(total_o2_from_h2_kg, WWTP_O2_DEMAND)

if WWTP_O2_DEMAND > 0:
    o2_reuse_pct = (o2_reuse_kg / WWTP_O2_DEMAND) * 100.0
else:
    o2_reuse_pct = 0.0

# =======================
# CO₂ AVOIDED PER HOUSE
# =======================

# Total useful heat demand of all houses assuming A-label
total_heat_demand_kwh = A_DEMAND_REF * TOTAL_HEATED_AREA_M2

# Gas input for that heat demand
if BOILER_EFFICIENCY > 0:
    gas_input_kwh = total_heat_demand_kwh / BOILER_EFFICIENCY
else:
    gas_input_kwh = 0.0

# Heat that can be substituted using *green* hydrogen
substituted_heat_kwh = min(heat_green_kWh, total_heat_demand_kwh)

# Total CO₂ avoided compared to natural gas
co2_avoided_vs_gas_total = substituted_heat_kwh * EMISSION_FACTOR_NG

# Area-weighted CO₂ avoided per m²
co2_avoided_per_m2 = (
    co2_avoided_vs_gas_total / TOTAL_HEATED_AREA_M2
    if TOTAL_HEATED_AREA_M2 > 0 else 0.0
)

# Per-house CO₂ avoided (area based)
co2_avoided_per_house_list = [
    co2_avoided_per_m2 * area for area in HOUSE_AREAS
]

# Average per-house CO₂ avoided
if len(co2_avoided_per_house_list) > 0:
    co2_avoided_per_house_avg = sum(co2_avoided_per_house_list) / len(co2_avoided_per_house_list)
else:
    co2_avoided_per_house_avg = 0.0

# Range (for potential explanation tooltip)
co2_avoided_house_min = min(co2_avoided_per_house_list) if co2_avoided_per_house_list else 0.0
co2_avoided_house_max = max(co2_avoided_per_house_list) if co2_avoided_per_house_list else 0.0

# =======================
# BATTERY UTILISATION
# =======================
battery_energy_to_el = discharged_kwh.sum()

if annual_total_kwh_to_el > 0:
    battery_util_pct = 100 * battery_energy_to_el / annual_total_kwh_to_el
else:
    battery_util_pct = 0.0

# =======================
# H₂ STORAGE MODEL (MONTHLY)
# =======================
h2_cap = float(H2_STORAGE_CAPACITY_KG)

# End-of-month SOC
h2_soc_kg_end = np.zeros(12)      # end-of-month state of charge (kg)
# Average SOC over the month (for utilisation KPI)
h2_soc_kg_avg = np.zeros(12)      # average SOC during the month (kg)

h2_stored_kg = np.zeros(12)       # surplus stored each month (kg)
h2_released_kg = np.zeros(12)     # H₂ taken from storage to cover deficits (kg)
h2_spill_kg = np.zeros(12)        # surplus that couldn't be stored (kg)
h2_unmet_kg = np.zeros(12)        # demand that couldn't be met even after storage (kg)

# Start from half-full buffer as a neutral assumption
soc_h2 = 0.5 * h2_cap

for m in range(12):
    soc_start = soc_h2           # SOC at start of month
    bal = float(monthly_balance[m])  # + = surplus, - = deficit

    if bal >= 0:
        # Surplus month: store up to capacity, spill the rest
        free_cap = max(h2_cap - soc_h2, 0.0)
        to_store = min(bal, free_cap)
        spill = max(bal - to_store, 0.0)

        soc_h2 += to_store
        h2_stored_kg[m] = to_store
        h2_spill_kg[m] = spill

    else:
        # Deficit month: release from storage, track unmet demand
        deficit = -bal
        from_store = min(deficit, soc_h2)
        unmet = max(deficit - from_store, 0.0)

        soc_h2 -= from_store
        h2_released_kg[m] = from_store
        h2_unmet_kg[m] = unmet

    # Record end-of-month SOC
    h2_soc_kg_end[m] = soc_h2
    # Record average SOC over the month
    h2_soc_kg_avg[m] = 0.5 * (soc_start + soc_h2)

# Monthly utilisation in % of buffer (based on average SOC)
if h2_cap > 0:
    h2_storage_util_pct_by_month = 100.0 * h2_soc_kg_avg / h2_cap
    h2_storage_util_pct_max = float(np.max(h2_storage_util_pct_by_month))
    h2_storage_util_pct_min = float(np.min(h2_storage_util_pct_by_month))
    h2_storage_util_pct_avg = float(np.mean(h2_storage_util_pct_by_month))
else:
    h2_storage_util_pct_by_month = np.zeros(12)
    h2_storage_util_pct_max = 0.0
    h2_storage_util_pct_min = 0.0
    h2_storage_util_pct_avg = 0.0

# Identify months with highest and lowest storage utilisation
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

if len(h2_storage_util_pct_by_month) == 12:
    idx_max = int(np.argmax(h2_storage_util_pct_by_month))
    idx_min = int(np.argmin(h2_storage_util_pct_by_month))
    h2_storage_month_max = month_labels[idx_max]
    h2_storage_month_min = month_labels[idx_min]
else:
    h2_storage_month_max = "-"
    h2_storage_month_min = "-"


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

# Some aggregate values for the new KPI cards
total_res_yield_kwh = float(monthly_res_kwh.sum())          # total renewable electricity available
total_el_input_kwh  = float(annual_total_kwh_to_el)         # electricity that actually reached EL
total_h2_kg         = float(hydrogen_kg_year)               # already computed above
total_co2_avoided   = float(co2_avoided_kg)
total_co2_grid      = float(grid_emitted_co2_kg)
total_waste_heat    = float(annual_waste_heat_kWh)


# Main layout: big map + vertical KPI column

main_col, right_col = st.columns([6, 2], gap="small", vertical_alignment="top")

# ===== MAIN COLUMN: MAP + BOTTOM KPI ROW =====
with main_col:
    # --- MAP COMPONENT (center, enlarged) ---
   
    with st.container():
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

        components.html(mapbox_html, height=600, scrolling=False)

    st.markdown("")  # small spacer

    # --- BOTTOM ROW: 5 KPI CARDS (SECONDARY) ---
    bottom_cols = st.columns(5, gap="small")

    # 1. Renewable Electricity Yield (from RES, not just what EL uses)
    with bottom_cols[0]:
        st.markdown(
            f"""
            <div class="dt-kpi-card">
                <div class="kpi-header">
                    <h6>Renewable Electricity Yield
                        <span class="tooltip">ⓘ
                            <span class="tooltiptext">
                                Annual renewable electricity allocated to hydrogen.
                                Includes wind + 30% of PV (as per project assumption).
                                This power supplies the EL directly first, then charges the battery.
                            </span>
                        </span>
                    </h6>
                </div>
                <p>{total_res_yield_kwh:,.0f}</p>
                <span>kWh/yr from PV + wind (allocated to H₂)</span>
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
        st.markdown(
            f"""
                <div class="dt-kpi-card">
                  <h6>O₂ Reused (WWTP)</h6>
                  <p>{o2_reuse_kg:,.0f}</p>
                  <span>kg/yr – {o2_reuse_pct:.3f}% of WWTP demand</span>
                </div>
                """,
            unsafe_allow_html=True,
        )

    # 4. CO₂ Emissions Avoided (total, vs grid heat for green H₂)
    with bottom_cols[3]:
        st.markdown(
            f"""
                <div class="dt-kpi-card">
                  <h6>CO₂ Emissions Avoided</h6>
                  <p>{co2_avoided_kg:,.0f}</p>
                  <span>kg CO₂/yr (green H₂ vs grid)</span>
                </div>
                """,
            unsafe_allow_html=True,
        )

    # 5. CO₂ Avoided per House (area-weighted)
    with bottom_cols[4]:
        st.markdown(
            f"""
                <div class="dt-kpi-card">
                  <h6>CO₂ Avoided per House</h6>
                  <p>{co2_avoided_per_house_avg:,.0f}</p>
                  <span>kg CO₂/house·yr (A-label, area-weighted)</span>
                </div>
                """,
            unsafe_allow_html=True,
        )

# ===== RIGHT COLUMN: 5 PRIORITY KPI CARDS (VERTICAL STACK) =====
with right_col:
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

    # 2. Seasonal Coverage of H₂ Demand
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

    # 3. H₂ Storage Utilisation
    if h2_cap > 0:
        headline_pct = h2_storage_util_pct_avg
        tooltip_text = (
            f"Average monthly fill level of the hydrogen buffer over the year. "
            f"Max: {h2_storage_util_pct_max:.0f}% in {h2_storage_month_max}. "
            f"Min: {h2_storage_util_pct_min:.0f}% in {h2_storage_month_min}."
        )
    else:
        headline_pct = 0.0
        tooltip_text = (
            "Hydrogen storage capacity is set to 0 kg in the current constants, "
            "so the buffer is not active in this scenario."
        )

    st.markdown(
        f"""
        <div class="dt-kpi-card">
          <h6>
            H₂ Storage Utilisation
            <span class="tooltip">
              ⓘ
              <span class="tooltiptext">{tooltip_text}</span>
            </span>
          </h6>
          <p>{headline_pct:.0f}%</p>
          <span>of {H2_STORAGE_CAPACITY_KG:.0f} kg buffer (monthly model)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. CO₂ Emissions (Grid)
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

    # 5. Battery system – diagnostics + button
    st.markdown("""
    <div class="dt-kpi-card">
      <div class="kpi-header">
        <h6>Battery system <span class="tooltip">ⓘ
          <span class="tooltiptext">
            Battery connected to PV + wind. Surplus RES first feeds the electrolyser 
            up to its cap; any remaining energy charges the battery. In shortages, 
            the battery can discharge to support EL operation.
          </span>
        </span></h6>
      </div>
      <p>Diagnostics view</p>
      <span>Shows monthly battery behaviour</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("View battery flows", key="btn_battery_diag"):
            st.session_state.show_battery_diag = True

# =======================
# BATTERY DIAGNOSTICS VIEW
# =======================

if st.session_state.get("show_battery_diag", False):

    st.markdown("---")
    st.markdown("### Battery energy flows (diagnostics)")
    st.caption(
        "Monthly breakdown of renewable electricity allocated to hydrogen, "
        "electrolyser cap, energy stored and discharged by the battery, "
        "renewables used for other site loads, and end-of-month state of charge."
    )

    # Build monthly table
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    df_battery = pd.DataFrame({
        "Month": month_labels,
        "RES available (kWh)": monthly_res_kwh,
        "EL cap (kWh)": max_monthly_kwh,
        "Direct to EL (kWh)": np.minimum(monthly_res_kwh, max_monthly_kwh),
        "Charged to battery (kWh)": charged_kwh,
        "Discharged from battery (kWh)": discharged_kwh,
        "RES for other site loads (kWh)": curtailed_kwh,
        "End-of-month SOC (kWh)": storage_soc_kwh,
    })

    st.dataframe(
        df_battery.style.format({
            "RES available (kWh)": "{:,.0f}",
            "EL cap (kWh)": "{:,.0f}",
            "Direct to EL (kWh)": "{:,.0f}",
            "Charged to battery (kWh)": "{:,.0f}",
            "Discharged from battery (kWh)": "{:,.0f}",
            "RES for other site loads (kWh)": "{:,.0f}",
            "End-of-month SOC (kWh)": "{:,.0f}",
        }),
        use_container_width=True,
    )

    # ---- Battery chart: RES for other loads + SOC (stacked) ----
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Ensure Month is ordered correctly
    df_battery["Month"] = pd.Categorical(
        df_battery["Month"],
        categories=months_order,
        ordered=True,
    )
    df_battery_sorted = df_battery.sort_values("Month")

    # Long format for Altair
    df_chart = df_battery_sorted[
        ["Month", "RES for other site loads (kWh)", "End-of-month SOC (kWh)"]
    ].melt(
        id_vars="Month",
        var_name="Metric",
        value_name="value",
    )

    # Numeric order so SOC is always stacked at the bottom
    metric_order = {
        "End-of-month SOC (kWh)": 0,          # bottom
        "RES for other site loads (kWh)": 1,  # top
    }
    df_chart["order_num"] = df_chart["Metric"].map(metric_order)

    battery_chart = (
        alt.Chart(df_chart)
        .mark_bar()
        .encode(
            x=alt.X("Month:O", sort=months_order, title="Month"),
            y=alt.Y("value:Q", stack="zero", title="Energy (kWh)"),
            color=alt.Color(
                "Metric:N",
                # legend order: SOC first, RES second
                sort=["End-of-month SOC (kWh)", "RES for other site loads (kWh)"],
            ),
            # actual stack order controlled by numeric column
            order=alt.Order("order_num:Q", sort="ascending"),
            tooltip=["Month", "Metric", alt.Tooltip("value:Q", format=",.0f")],
        )
        .properties(height=260)
    )

    st.altair_chart(battery_chart, use_container_width=True)

    if st.button("Close battery view", key="btn_close_battery_diag"):
        st.session_state.show_battery_diag = False

