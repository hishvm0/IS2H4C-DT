import streamlit as st
import pandas as pd
import numpy as np
import calendar
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="What-If Energy Calculator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =======================
# STYLES
# =======================
st.markdown("""
<style>
[data-testid="AppViewContainer"],
[data-testid="stAppViewContainer"] {
  background-color:#0e1117;
  color:#fafafa;
}

[data-testid="stSidebar"] {
  background-color:#40444d;
}

.metric-card {
  background:#26264d;
  padding:15px;
  border-radius:10px;
  margin-bottom:10px;
}

.metric-card h3 {
  font-size:1rem;
  margin:0 0 5px 0;
  color:#A3A6F7;
}

.metric-card p {
  font-size:1.5rem;
  margin:0;
  font-weight:bold;
  color:#ffffff;
}

.metric-card span {
  font-size:0.9rem;
  color:#bbbbbb;
}

.comparison-positive {
  color:#65d26e;
}

.comparison-negative {
  color:#ff6b6b;
}

.house-card {
  background:#1a1a2e;
  padding:12px;
  border-radius:8px;
  margin-bottom:8px;
  border-left:3px solid #A3A6F7;
}

.house-card h4 {
  margin:0 0 8px 0;
  color:#A3A6F7;
  font-size:0.95rem;
}

.scenario-badge {
  display:inline-block;
  padding:4px 12px;
  border-radius:12px;
  font-size:0.8rem;
  font-weight:bold;
  margin-right:8px;
}

.badge-baseline {
  background:#404040;
  color:#ffffff;
}

.badge-whatif {
  background:#4a148c;
  color:#ffffff;
}
</style>
""", unsafe_allow_html=True)

# =======================
# LOAD BASE DATA
# =======================
@st.cache_data
def load_base_constants():
    df = pd.read_csv("dashboard/data_constants.csv", index_col=0)
    return df

DATA = load_base_constants()

# =======================
# INITIALIZE SESSION STATE
# =======================
if "houses" not in st.session_state:
    # Initialize with baseline houses
    st.session_state.houses = [
        {
            "id": 1,
            "name": "Albardastraat 34",
            "type": "Residential",
            "area_m2": 230,
            "h2_demand_kg": 615,
        },
        {
            "id": 2,
            "name": "Albardastraat 31",
            "type": "Residential",
            "area_m2": 229,
            "h2_demand_kg": 752,
        },
        {
            "id": 3,
            "name": "Albardastraat 20",
            "type": "Community centre",
            "area_m2": 478,
            "h2_demand_kg": 2735,
        },
        {
            "id": 4,
            "name": "Albardastraat 46",
            "type": "Residential",
            "area_m2": 597,
            "h2_demand_kg": 820,
        },
    ]

if "energy_params" not in st.session_state:
    st.session_state.energy_params = {
        "electrolyzer_kw": float(DATA.loc["el_rated_power_kw", "value"]),
        "pv_capacity_kw": float(DATA.loc["pv_capacity_kw", "value"]),
        "wind_capacity_kw": float(DATA.loc["wind_capacity_kw", "value"]),
        "battery_capacity_kwh": float(DATA.loc["battery_cap_baseline_kwh", "value"]),
        "h2_storage_kg": float(DATA.loc["h2_storage_capacity_kg", "value"]),
        "pv_allocation_factor": 0.30,
    }

if "next_house_id" not in st.session_state:
    st.session_state.next_house_id = 5

# =======================
# CALCULATION FUNCTIONS
# =======================
def calculate_system_performance(houses, energy_params, operating_hours=8, energy_source="Energy Mix (Solar + Wind)"):
    """
    Calculate system performance based on custom house configuration and energy parameters.
    """
    # Extract parameters
    ELECTROLYZER_KW = energy_params["electrolyzer_kw"]
    pv_capacity_kw = energy_params["pv_capacity_kw"]
    wind_capacity_kw = energy_params["wind_capacity_kw"]
    bat_cap_kwh = energy_params["battery_capacity_kwh"]
    h2_storage_kg = energy_params["h2_storage_kg"]
    PV_ALLOCATION_FACTOR = energy_params["pv_allocation_factor"]

    # Constants
    SEC = float(DATA.loc["sec_kwh_per_kg", "value"])
    LHV_H2 = float(DATA.loc["lhv_h2_kwh_per_kg", "value"])
    EMISSION_FACTOR_GRID = float(DATA.loc["em_factor_grid_kg_per_kwh", "value"])
    EMISSION_FACTOR_NG = float(DATA.loc["em_factor_ng_kg_per_kwh", "value"])
    ETA_CHG = float(DATA.loc["battery_eta_charge", "value"])
    ETA_DIS = float(DATA.loc["battery_eta_discharge", "value"])
    O2_PER_KG_H2 = float(DATA.loc["o2_per_kg_h2", "value"])
    WWTP_O2_DEMAND = float(DATA.loc["wwtp_o2_demand_annual", "value"])

    # Calculate total demand from houses
    total_area_m2 = sum([h["area_m2"] for h in houses])
    annual_h2_demand = sum([h["h2_demand_kg"] for h in houses])

    # Monthly capacity factors
    solar_cf = np.array([0.0425, 0.0752, 0.1210, 0.1656, 0.1701, 0.1755,
                         0.1672, 0.1544, 0.1337, 0.0896, 0.0539, 0.0364])
    wind_cf = np.array([0.3127, 0.3007, 0.1936, 0.2449, 0.1145, 0.1460,
                        0.1453, 0.1392, 0.1760, 0.1580, 0.1969, 0.2682])

    demand_share_arr = np.array([0.1969, 0.1615, 0.1240, 0.0955, 0.0389, 0.0135,
                                 0.0140, 0.0130, 0.0186, 0.0506, 0.1070, 0.1667])

    # Time bases
    days_in_month = np.array([calendar.monthrange(2025, m)[1] for m in range(1, 13)])
    hours_in_month_calendar = days_in_month * 24

    hours_per_month_weekdays = np.array([
        len(pd.bdate_range(f"2025-{m:02d}-01", f"2025-{m:02d}-{days_in_month[m-1]}")) * operating_hours
        for m in range(1, 13)
    ])

    # Monthly energy available
    pv_capacity_effective_kw = pv_capacity_kw * PV_ALLOCATION_FACTOR
    monthly_solar_kwh_raw = pv_capacity_effective_kw * solar_cf * hours_in_month_calendar
    monthly_wind_kwh_raw = wind_capacity_kw * wind_cf * hours_in_month_calendar
    monthly_res_kwh_raw = monthly_solar_kwh_raw + monthly_wind_kwh_raw

    max_monthly_kwh = ELECTROLYZER_KW * hours_per_month_weekdays

    # Apply energy source choice
    if energy_source == "Wind Only":
        monthly_res_kwh = monthly_wind_kwh_raw
    elif energy_source == "Solar Only":
        monthly_res_kwh = monthly_solar_kwh_raw
    elif energy_source in ["Energy Mix (Solar + Wind)", "Solar + Wind (Baseline)"]:
        monthly_res_kwh = monthly_res_kwh_raw
    else:  # "Grid Only"
        monthly_res_kwh = np.zeros(12)

    # Battery model
    usable_kwh = np.zeros(12)
    monthly_grid_kwh = np.zeros(12)
    storage_soc_kwh = np.zeros(12)
    charged_kwh = np.zeros(12)
    discharged_kwh = np.zeros(12)
    curtailed_kwh = np.zeros(12)
    el_unserved_kwh = np.zeros(12)

    if energy_source == "Grid Only":
        usable_kwh = max_monthly_kwh.copy()
        monthly_grid_kwh = max_monthly_kwh.copy()
    else:
        soc = 0.0
        for m in range(12):
            cap_m = max_monthly_kwh[m]
            res_m = monthly_res_kwh[m]

            # Direct feed
            direct = min(res_m, cap_m)
            usable = direct

            # Store surplus
            surplus = max(0.0, res_m - direct)
            if bat_cap_kwh > 0:
                room = bat_cap_kwh - soc
                if room > 0:
                    charge_in = min(surplus, room / ETA_CHG)
                    soc += charge_in * ETA_CHG
                    charged_kwh[m] = charge_in
                    curtailed_kwh[m] = surplus - charge_in
                else:
                    curtailed_kwh[m] = surplus
            else:
                curtailed_kwh[m] = surplus

            # Discharge to cover deficit
            deficit = max(0.0, cap_m - usable)
            if soc > 0 and deficit > 0:
                deliverable = soc * ETA_DIS
                discharge = min(deficit, deliverable)
                if discharge > 0:
                    soc -= discharge / ETA_DIS
                    usable += discharge
                    discharged_kwh[m] = discharge

            el_unserved_kwh[m] = max(0.0, cap_m - usable)
            storage_soc_kwh[m] = soc
            usable_kwh[m] = usable

    # H2 production and demand
    monthly_h2_production = usable_kwh / SEC
    monthly_h2_demand = demand_share_arr * annual_h2_demand
    monthly_balance = monthly_h2_production - monthly_h2_demand

    # KPIs
    annual_total_kwh_to_el = usable_kwh.sum()
    annual_grid_kwh_to_el = monthly_grid_kwh.sum()
    annual_res_kwh_to_el = annual_total_kwh_to_el - annual_grid_kwh_to_el

    hydrogen_kg_year = annual_total_kwh_to_el / SEC
    green_h2_kg = annual_res_kwh_to_el / SEC

    seasonal_coverage_pct = (monthly_h2_production.sum() / annual_h2_demand) * 100 if annual_h2_demand > 0 else 0

    # CO2 calculations
    heat_green_kWh = green_h2_kg * LHV_H2
    co2_avoided_kg = heat_green_kWh * EMISSION_FACTOR_GRID
    grid_emitted_co2_kg = annual_grid_kwh_to_el * EMISSION_FACTOR_GRID

    # O2 reuse
    total_o2_from_h2_kg = hydrogen_kg_year * O2_PER_KG_H2
    o2_reuse_kg = min(total_o2_from_h2_kg, WWTP_O2_DEMAND)
    o2_reuse_pct = (o2_reuse_kg / WWTP_O2_DEMAND) * 100.0 if WWTP_O2_DEMAND > 0 else 0.0

    # Waste heat
    HEAT_RECOVERY_FRAC = float(DATA.loc["heat_recovery_frac", "value"])
    annual_waste_heat_kWh = annual_total_kwh_to_el * HEAT_RECOVERY_FRAC

    # Battery utilization
    battery_energy_to_el = discharged_kwh.sum()
    battery_util_pct = 100 * battery_energy_to_el / annual_total_kwh_to_el if annual_total_kwh_to_el > 0 else 0.0

    return {
        "hydrogen_production_kg": hydrogen_kg_year,
        "seasonal_coverage_pct": seasonal_coverage_pct,
        "co2_avoided_kg": co2_avoided_kg,
        "co2_emissions_grid_kg": grid_emitted_co2_kg,
        "annual_h2_demand": annual_h2_demand,
        "total_area_m2": total_area_m2,
        "monthly_h2_production": monthly_h2_production,
        "monthly_h2_demand": monthly_h2_demand,
        "monthly_balance": monthly_balance,
        "o2_reuse_kg": o2_reuse_kg,
        "o2_reuse_pct": o2_reuse_pct,
        "waste_heat_kwh": annual_waste_heat_kWh,
        "battery_util_pct": battery_util_pct,
        "annual_res_kwh": monthly_res_kwh.sum(),
        "curtailed_kwh": curtailed_kwh.sum(),
    }

# =======================
# SIDEBAR: CONTROLS
# =======================
st.sidebar.markdown("## 🔮 What-If Calculator")
st.sidebar.markdown("Modify system parameters and see the impact on performance.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Energy System")

with st.sidebar.expander("🔧 System Capacity", expanded=False):
    electrolyzer_kw = st.number_input(
        "Electrolyzer Power (kW)",
        min_value=10.0,
        max_value=500.0,
        value=st.session_state.energy_params["electrolyzer_kw"],
        step=10.0,
        help="Rated power of the electrolyzer"
    )

    pv_capacity_kw = st.number_input(
        "PV Capacity (kWp)",
        min_value=0.0,
        max_value=5000.0,
        value=st.session_state.energy_params["pv_capacity_kw"],
        step=50.0,
        help="Total installed PV capacity"
    )

    pv_allocation = st.slider(
        "PV Allocation Factor",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.energy_params["pv_allocation_factor"],
        step=0.05,
        help="Fraction of PV capacity allocated to H2 system"
    )

    wind_capacity_kw = st.number_input(
        "Wind Capacity (kW)",
        min_value=0.0,
        max_value=500.0,
        value=st.session_state.energy_params["wind_capacity_kw"],
        step=10.0,
        help="Installed wind turbine capacity"
    )

    battery_capacity_kwh = st.number_input(
        "Battery Capacity (kWh)",
        min_value=0.0,
        max_value=5000.0,
        value=st.session_state.energy_params["battery_capacity_kwh"],
        step=100.0,
        help="Energy storage capacity"
    )

    h2_storage_kg = st.number_input(
        "H₂ Storage (kg)",
        min_value=0.0,
        max_value=500.0,
        value=st.session_state.energy_params["h2_storage_kg"],
        step=10.0,
        help="Hydrogen storage buffer capacity"
    )

    if st.button("Apply Energy Changes"):
        st.session_state.energy_params = {
            "electrolyzer_kw": electrolyzer_kw,
            "pv_capacity_kw": pv_capacity_kw,
            "wind_capacity_kw": wind_capacity_kw,
            "battery_capacity_kwh": battery_capacity_kwh,
            "h2_storage_kg": h2_storage_kg,
            "pv_allocation_factor": pv_allocation,
        }
        st.success("Energy parameters updated!")
        st.rerun()

st.sidebar.markdown("---")

with st.sidebar.expander("⚙️ Operating Parameters", expanded=False):
    operating_hours = st.slider(
        "Operating Hours/Day",
        min_value=1,
        max_value=24,
        value=8,
        help="Electrolyzer hours per weekday"
    )

    energy_source = st.selectbox(
        "Energy Source",
        options=[
            "Energy Mix (Solar + Wind)",
            "Wind Only",
            "Solar Only",
            "Grid Only",
        ],
        index=0
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏠 House Management")

with st.sidebar.expander("➕ Add New House", expanded=False):
    new_house_name = st.text_input("House Name", value=f"New House {st.session_state.next_house_id}")
    new_house_type = st.selectbox("Type", ["Residential", "Community centre", "Office", "Commercial"])
    new_house_area = st.number_input("Floor Area (m²)", min_value=50, max_value=2000, value=200, step=10)

    # Estimate H2 demand based on area
    A_DEMAND_REF = float(DATA.loc["a_demand_ref_kwh_per_m2", "value"])
    BOILER_EFF = float(DATA.loc["boiler_efficiency", "value"])
    LHV_H2 = float(DATA.loc["lhv_h2_kwh_per_kg", "value"])
    estimated_h2 = (new_house_area * A_DEMAND_REF / BOILER_EFF) / LHV_H2

    new_house_h2 = st.number_input(
        "Annual H₂ Demand (kg)",
        min_value=0.0,
        max_value=10000.0,
        value=float(estimated_h2),
        step=10.0,
        help="Estimated based on floor area"
    )

    if st.button("Add House"):
        st.session_state.houses.append({
            "id": st.session_state.next_house_id,
            "name": new_house_name,
            "type": new_house_type,
            "area_m2": new_house_area,
            "h2_demand_kg": new_house_h2,
        })
        st.session_state.next_house_id += 1
        st.success(f"Added {new_house_name}")
        st.rerun()

# =======================
# MAIN CONTENT
# =======================
st.title("🔮 What-If Energy Calculator")
st.markdown("**Explore how changes to the energy system and building portfolio affect performance**")

# Calculate baseline (original configuration)
baseline_houses = [
    {"id": 1, "name": "Albardastraat 34", "type": "Residential", "area_m2": 230, "h2_demand_kg": 615},
    {"id": 2, "name": "Albardastraat 31", "type": "Residential", "area_m2": 229, "h2_demand_kg": 752},
    {"id": 3, "name": "Albardastraat 20", "type": "Community centre", "area_m2": 478, "h2_demand_kg": 2735},
    {"id": 4, "name": "Albardastraat 46", "type": "Residential", "area_m2": 597, "h2_demand_kg": 820},
]

baseline_energy = {
    "electrolyzer_kw": float(DATA.loc["el_rated_power_kw", "value"]),
    "pv_capacity_kw": float(DATA.loc["pv_capacity_kw", "value"]),
    "wind_capacity_kw": float(DATA.loc["wind_capacity_kw", "value"]),
    "battery_capacity_kwh": float(DATA.loc["battery_cap_baseline_kwh", "value"]),
    "h2_storage_kg": float(DATA.loc["h2_storage_capacity_kg", "value"]),
    "pv_allocation_factor": 0.30,
}

baseline_results = calculate_system_performance(baseline_houses, baseline_energy, operating_hours, energy_source)
whatif_results = calculate_system_performance(st.session_state.houses, st.session_state.energy_params, operating_hours, energy_source)

# =======================
# HOUSE PORTFOLIO
# =======================
st.markdown("---")
st.markdown("## 🏘️ Building Portfolio")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"**Total Buildings:** {len(st.session_state.houses)} | **Total Area:** {sum([h['area_m2'] for h in st.session_state.houses]):,.0f} m²")

with col2:
    if st.button("🔄 Reset to Baseline"):
        st.session_state.houses = baseline_houses.copy()
        st.session_state.next_house_id = 5
        st.rerun()

# Display houses in cards with edit/remove options
house_cols = st.columns(2)
for idx, house in enumerate(st.session_state.houses):
    with house_cols[idx % 2]:
        with st.container():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div class="house-card">
                    <h4>🏠 {house['name']}</h4>
                    <p style="margin:0; color:#ccc; font-size:0.85rem;">{house['type']}</p>
                    <p style="margin:4px 0; font-size:0.9rem;">Area: <strong>{house['area_m2']:.0f} m²</strong></p>
                    <p style="margin:0; font-size:0.9rem;">H₂ Demand: <strong>{house['h2_demand_kg']:.0f} kg/yr</strong></p>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("🗑️", key=f"del_{house['id']}", help="Remove house"):
                    st.session_state.houses = [h for h in st.session_state.houses if h['id'] != house['id']]
                    st.rerun()

# =======================
# COMPARISON RESULTS
# =======================
st.markdown("---")
st.markdown("## 📊 Performance Comparison")

def format_comparison(whatif_val, baseline_val, unit="", invert=False):
    """Format comparison with color coding. If invert=True, negative change is good."""
    diff = whatif_val - baseline_val
    pct_change = (diff / baseline_val * 100) if baseline_val != 0 else 0

    is_positive = (diff > 0) if not invert else (diff < 0)
    color_class = "comparison-positive" if is_positive else "comparison-negative"
    arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"

    return f"""
    <div style="margin-top:5px;">
        <span class="{color_class}" style="font-size:0.9rem;">
            {arrow} {abs(diff):,.0f} {unit} ({abs(pct_change):.1f}%)
        </span>
    </div>
    """

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>H₂ Demand</h3>
        <div>
            <span class="scenario-badge badge-baseline">Baseline</span>
            <p style="display:inline; font-size:1.2rem;">{baseline_results['annual_h2_demand']:,.0f}</p>
        </div>
        <div style="margin-top:8px;">
            <span class="scenario-badge badge-whatif">What-If</span>
            <p style="display:inline; font-size:1.2rem;">{whatif_results['annual_h2_demand']:,.0f}</p>
        </div>
        {format_comparison(whatif_results['annual_h2_demand'], baseline_results['annual_h2_demand'], "kg/yr")}
        <span>Annual hydrogen demand</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>H₂ Production</h3>
        <div>
            <span class="scenario-badge badge-baseline">Baseline</span>
            <p style="display:inline; font-size:1.2rem;">{baseline_results['hydrogen_production_kg']:,.0f}</p>
        </div>
        <div style="margin-top:8px;">
            <span class="scenario-badge badge-whatif">What-If</span>
            <p style="display:inline; font-size:1.2rem;">{whatif_results['hydrogen_production_kg']:,.0f}</p>
        </div>
        {format_comparison(whatif_results['hydrogen_production_kg'], baseline_results['hydrogen_production_kg'], "kg/yr")}
        <span>Annual hydrogen production</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Seasonal Coverage</h3>
        <div>
            <span class="scenario-badge badge-baseline">Baseline</span>
            <p style="display:inline; font-size:1.2rem;">{baseline_results['seasonal_coverage_pct']:.1f}%</p>
        </div>
        <div style="margin-top:8px;">
            <span class="scenario-badge badge-whatif">What-If</span>
            <p style="display:inline; font-size:1.2rem;">{whatif_results['seasonal_coverage_pct']:.1f}%</p>
        </div>
        {format_comparison(whatif_results['seasonal_coverage_pct'], baseline_results['seasonal_coverage_pct'], "%")}
        <span>Demand met by production</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>CO₂ Avoided</h3>
        <div>
            <span class="scenario-badge badge-baseline">Baseline</span>
            <p style="display:inline; font-size:1.2rem;">{baseline_results['co2_avoided_kg']:,.0f}</p>
        </div>
        <div style="margin-top:8px;">
            <span class="scenario-badge badge-whatif">What-If</span>
            <p style="display:inline; font-size:1.2rem;">{whatif_results['co2_avoided_kg']:,.0f}</p>
        </div>
        {format_comparison(whatif_results['co2_avoided_kg'], baseline_results['co2_avoided_kg'], "kg/yr")}
        <span>CO₂ emissions avoided</span>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Grid Emissions</h3>
        <div>
            <span class="scenario-badge badge-baseline">Baseline</span>
            <p style="display:inline; font-size:1.2rem;">{baseline_results['co2_emissions_grid_kg']:,.0f}</p>
        </div>
        <div style="margin-top:8px;">
            <span class="scenario-badge badge-whatif">What-If</span>
            <p style="display:inline; font-size:1.2rem;">{whatif_results['co2_emissions_grid_kg']:,.0f}</p>
        </div>
        {format_comparison(whatif_results['co2_emissions_grid_kg'], baseline_results['co2_emissions_grid_kg'], "kg/yr", invert=True)}
        <span>CO₂ from grid electricity</span>
    </div>
    """, unsafe_allow_html=True)

# =======================
# CHARTS
# =======================
st.markdown("---")
st.markdown("## 📈 Monthly Analysis")

tab1, tab2, tab3 = st.tabs(["Monthly Balance", "System Parameters", "Additional Metrics"])

with tab1:
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Baseline Scenario", "What-If Scenario"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    # Baseline
    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=baseline_results['monthly_h2_production'],
            name="Production (Baseline)",
            marker_color="#4a90e2",
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=baseline_results['monthly_h2_demand'],
            name="Demand (Baseline)",
            marker_color="#e24a4a",
            showlegend=True
        ),
        row=1, col=1
    )

    # What-If
    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=whatif_results['monthly_h2_production'],
            name="Production (What-If)",
            marker_color="#7e4ae2",
            showlegend=True
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=whatif_results['monthly_h2_demand'],
            name="Demand (What-If)",
            marker_color="#e2a14a",
            showlegend=True
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        barmode='group',
        template="plotly_dark",
        showlegend=True
    )

    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=1, col=2)
    fig.update_yaxes(title_text="H₂ (kg)", row=1, col=1)
    fig.update_yaxes(title_text="H₂ (kg)", row=1, col=2)

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Energy system parameters comparison
    params_df = pd.DataFrame({
        "Parameter": [
            "Electrolyzer (kW)",
            "PV Capacity (kWp)",
            "Wind Capacity (kW)",
            "Battery (kWh)",
            "H₂ Storage (kg)"
        ],
        "Baseline": [
            baseline_energy["electrolyzer_kw"],
            baseline_energy["pv_capacity_kw"],
            baseline_energy["wind_capacity_kw"],
            baseline_energy["battery_capacity_kwh"],
            baseline_energy["h2_storage_kg"]
        ],
        "What-If": [
            st.session_state.energy_params["electrolyzer_kw"],
            st.session_state.energy_params["pv_capacity_kw"],
            st.session_state.energy_params["wind_capacity_kw"],
            st.session_state.energy_params["battery_capacity_kwh"],
            st.session_state.energy_params["h2_storage_kg"]
        ]
    })

    params_df["Change (%)"] = ((params_df["What-If"] - params_df["Baseline"]) / params_df["Baseline"] * 100).round(1)

    st.dataframe(
        params_df.style.format({
            "Baseline": "{:,.0f}",
            "What-If": "{:,.0f}",
            "Change (%)": "{:+.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric(
            "Waste Heat Recovery",
            f"{whatif_results['waste_heat_kwh']:,.0f} kWh/yr",
            delta=f"{whatif_results['waste_heat_kwh'] - baseline_results['waste_heat_kwh']:,.0f} kWh/yr"
        )

    with col_b:
        st.metric(
            "O₂ Reuse",
            f"{whatif_results['o2_reuse_kg']:,.0f} kg/yr",
            delta=f"{whatif_results['o2_reuse_kg'] - baseline_results['o2_reuse_kg']:,.0f} kg/yr"
        )

    with col_c:
        st.metric(
            "Battery Utilization",
            f"{whatif_results['battery_util_pct']:.1f}%",
            delta=f"{whatif_results['battery_util_pct'] - baseline_results['battery_util_pct']:.1f}%"
        )

    st.markdown("---")

    col_d, col_e = st.columns(2)

    with col_d:
        st.metric(
            "Annual RES Available",
            f"{whatif_results['annual_res_kwh']:,.0f} kWh/yr",
            delta=f"{whatif_results['annual_res_kwh'] - baseline_results['annual_res_kwh']:,.0f} kWh/yr"
        )

    with col_e:
        st.metric(
            "Curtailed Energy",
            f"{whatif_results['curtailed_kwh']:,.0f} kWh/yr",
            delta=f"{whatif_results['curtailed_kwh'] - baseline_results['curtailed_kwh']:,.0f} kWh/yr",
            delta_color="inverse"
        )

# =======================
# INSIGHTS & RECOMMENDATIONS
# =======================
st.markdown("---")
st.markdown("## 💡 Insights")

insights = []

# Coverage analysis
if whatif_results['seasonal_coverage_pct'] < 90:
    insights.append(f"⚠️ **Low Coverage**: System only meets {whatif_results['seasonal_coverage_pct']:.1f}% of demand. Consider increasing electrolyzer capacity or renewable generation.")
elif whatif_results['seasonal_coverage_pct'] > 110:
    insights.append(f"⚠️ **Oversized System**: Production exceeds demand by {whatif_results['seasonal_coverage_pct'] - 100:.1f}%. Consider adding more houses or reducing capacity.")
else:
    insights.append(f"✅ **Good Balance**: System coverage of {whatif_results['seasonal_coverage_pct']:.1f}% is within optimal range (90-110%).")

# Demand change
demand_change = whatif_results['annual_h2_demand'] - baseline_results['annual_h2_demand']
if abs(demand_change) > 100:
    insights.append(f"📊 **Demand Change**: Total demand changed by {demand_change:+,.0f} kg/yr ({demand_change/baseline_results['annual_h2_demand']*100:+.1f}%) compared to baseline.")

# CO2 impact
co2_change = whatif_results['co2_avoided_kg'] - baseline_results['co2_avoided_kg']
if co2_change > 1000:
    insights.append(f"🌱 **Improved Sustainability**: CO₂ savings increased by {co2_change:,.0f} kg/yr compared to baseline.")
elif co2_change < -1000:
    insights.append(f"⚠️ **Reduced Sustainability**: CO₂ savings decreased by {abs(co2_change):,.0f} kg/yr compared to baseline.")

# House count change
house_change = len(st.session_state.houses) - len(baseline_houses)
if house_change > 0:
    insights.append(f"🏘️ **Portfolio Expansion**: Added {house_change} building(s) to the system.")
elif house_change < 0:
    insights.append(f"🏘️ **Portfolio Reduction**: Removed {abs(house_change)} building(s) from the system.")

# Display insights
for insight in insights:
    st.markdown(insight)

# =======================
# EXPORT OPTIONS
# =======================
st.markdown("---")

export_col1, export_col2 = st.columns(2)

with export_col1:
    if st.button("📥 Export What-If Results (CSV)"):
        # Create comprehensive export dataframe
        export_data = {
            "Metric": [
                "Annual H₂ Demand (kg/yr)",
                "H₂ Production (kg/yr)",
                "Seasonal Coverage (%)",
                "CO₂ Avoided (kg/yr)",
                "Grid Emissions (kg/yr)",
                "Waste Heat (kWh/yr)",
                "O₂ Reuse (kg/yr)",
                "Number of Buildings",
                "Total Floor Area (m²)",
                "Electrolyzer Capacity (kW)",
                "PV Capacity (kWp)",
                "Wind Capacity (kW)",
                "Battery Capacity (kWh)",
                "H₂ Storage (kg)",
            ],
            "Baseline": [
                baseline_results['annual_h2_demand'],
                baseline_results['hydrogen_production_kg'],
                baseline_results['seasonal_coverage_pct'],
                baseline_results['co2_avoided_kg'],
                baseline_results['co2_emissions_grid_kg'],
                baseline_results['waste_heat_kwh'],
                baseline_results['o2_reuse_kg'],
                len(baseline_houses),
                baseline_results['total_area_m2'],
                baseline_energy['electrolyzer_kw'],
                baseline_energy['pv_capacity_kw'],
                baseline_energy['wind_capacity_kw'],
                baseline_energy['battery_capacity_kwh'],
                baseline_energy['h2_storage_kg'],
            ],
            "What-If": [
                whatif_results['annual_h2_demand'],
                whatif_results['hydrogen_production_kg'],
                whatif_results['seasonal_coverage_pct'],
                whatif_results['co2_avoided_kg'],
                whatif_results['co2_emissions_grid_kg'],
                whatif_results['waste_heat_kwh'],
                whatif_results['o2_reuse_kg'],
                len(st.session_state.houses),
                whatif_results['total_area_m2'],
                st.session_state.energy_params['electrolyzer_kw'],
                st.session_state.energy_params['pv_capacity_kw'],
                st.session_state.energy_params['wind_capacity_kw'],
                st.session_state.energy_params['battery_capacity_kwh'],
                st.session_state.energy_params['h2_storage_kg'],
            ]
        }

        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False)

        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="what_if_comparison.csv",
            mime="text/csv"
        )

with export_col2:
    st.markdown("**Quick Actions:**")
    if st.button("📋 Copy Scenario to Main Dashboard"):
        st.info("This feature will integrate with the main dashboard in the next update.")
