# Digital Twin Dashboard — Indicators Documentation

This document summarizes the four indicator cards used in the DT Dashboard for assessing the hydrogen-based energy systems. Each indicator reflects a critical dimension of system performance, and all four are dynamically responsive to user input from the sidebar, including energy source selection and operational hours. Together, they provide an interconnected picture of production, efficiency, emissions, and seasonal performance.

---

## 1. Hydrogen Production (kg/year)

**Definition:**  
Total hydrogen produced annually by the electrolyzer, based on user-selected operational hours.

**Objective:**  
Estimate the total usable hydrogen generated from available electricity sources.

**Contribution:**  
Feeds directly into KPIs 2–4, providing the basis for energy service delivery.

**Assumptions:**
- Electrolyzer capacity = 70 kW (fixed)  
- Operating days = 260 days/year (weekdays)  
- Electrolyzer SEC = 52.5 kWh/kg H₂  

**Formula:**  
\[
H_2 = \frac{P_{el} \times h_{op} \times d_{op}}{SEC}
\]

---

## 2. CO₂ Emissions Avoided (kg/year)

**Definition:**  
CO₂ emissions avoided by using green hydrogen instead of grid electricity for heating.

**Objective:**  
Show environmental benefit of using RES-based hydrogen.

**Contribution:**  
Quantifies climate impact reduction, useful for scenario comparison and communication.

**Assumptions:**
- Grid emission factor = 0.388 kg CO₂/kWh  
- SEC = 52.5 kWh/kg H₂  
- LHV of hydrogen = 33.3 kWh/kg  

**Formula:**  
\[
CO_{2,avoided} = H_2 \times LHV_{H_2} \times EF_{grid}
\]

---

## 3. Heat from Green H₂ (kWh/year)

**Definition:**  
Total annual heat available from renewable hydrogen.

**Objective:**  
Assess renewable heating potential compared to residential demand.

**Contribution:**  
Supports understanding of building-level coverage, reflects benefit to households.

**Assumptions:**
- Only green (renewable-based) hydrogen is considered  
- LHV of H₂ = 33.3 kWh/kg  

**Formula:**  
\[
Q_{H_2} = H_2 \times LHV_{H_2}
\]

---

## 4. Seasonal Coverage (%)

**Definition:**  
Percentage of annual hydrogen demand that can be seasonally met by monthly green hydrogen production.

**Objective:**  
Capture mismatch between intermittent RES supply and steady demand.

**Contribution:**  
Informs the need for storage and timing strategies.

**Assumptions:**
- Monthly RES and demand profiles are normalized  
- Limited by electrolyzer capacity and operational hours  

**Formula:**  
\[
Coverage_m = \frac{H_{2,prod}(m)}{H_{2,demand}(m)} \times 100
\]

---

## Sidebar Control & Interconnectedness

User selections from the sidebar—such as energy source (wind, solar, grid, mix), renewable share, and operational hours—dynamically influence all indicators.

- **Indicator 1** is directly driven by these inputs.  
- **Indicators 2 and 3** rely on 1’s output and filter it by renewable contribution.  
- **Indicator 4** applies the same inputs month-by-month to check how much of the demand can be met throughout the year.

This interconnected structure helps users understand bottlenecks and how different configurations affect system sustainability, coverage, and emissions.

---

## Monthly Hydrogen Production vs Demand (Line Chart)

**Definition:**  
Time-series comparison of monthly hydrogen production (from the electrolyzer) and monthly hydrogen demand (from households/crematoria).

**Objective:**  
Visualize seasonal mismatches between hydrogen supply and demand.  

**Decision Support:**  
- Assess whether RES capacity and electrolyzer operation meet demand.  
- Identify storage needs or backup supply.  
- Show impacts of energy-source choices and EL schedules.

**Formulas**

Monthly Production (kg):
\[
H_{2,prod}(m) = \frac{\min(E_{avail}(m), P_{EL,max} \times h_{op}(m))}{SEC}
\]

Monthly Demand (kg):
\[
H_{2,dem}(m) = D_{share}(m) \times H_{2,annual}
\]

**Assumptions:**
- Renewable capacity factors (solar/wind) are averaged monthly.  
- Electrolyzer instantly consumes available energy up to rating.  
- Demand profile fixed and stable across years.  
- No storage carry-over (surplus not retained).

---

## Hydrogen Storage Operation — Monthly Balance & SOC (Bar + Line Chart)

Combined visualization of monthly surplus/deficit (bars) and cumulative hydrogen storage level (line).

**Objective:**  
Evaluate whether seasonal imbalances can be balanced by storage; SOC curve indicates required storage size and interruptions.

**Decision Support**
- Identify minimum required storage capacity to avoid shortages.  
- Compare scenarios (added RES, extended EL hours, grid backup).  
- Show when storage fills (surplus) or empties (deficit).

**Formulas**

Monthly Balance:
\[
B(m) = H_{2,prod}(m) - H_{2,dem}(m)
\]

Cumulative Storage Level (SOC):
\[
SOC(m) = SOC(m-1) + B(m)
\]

Required Storage Capacity:
\[
C_{req} = \max(SOC) - \min(SOC)
\]

**Assumptions:**
- Ideal storage (no losses, no inefficiency).  
- Surpluses stored and available later without limits.  
- Deficits draw from storage; negative SOC → interruptions.  
- Electrolyzer hours fixed per scenario.

---

## O₂ Reuse — Electricity Saved

**Definition:**  
Electricity savings at the wastewater treatment plant (WWTP) from reusing oxygen byproduct from electrolysis.

**Objective:**  
Highlight industrial symbiosis benefit between hydrogen production and wastewater treatment.

**Contribution:**  
Demonstrates circularity and indirect energy savings.

**Assumptions:**
- 1 kg H₂ → 8 kg O₂ (stoichiometric)  
- 30% of produced O₂ reused by WWTP  
- Aeration electricity intensity = 0.5 kWh/kg O₂  
- Reuse logistics ignored  
- Annualized, based on simulated monthly H₂ production  

**Formula:**  
\[
E_{saved} = H_2 \times 8 \times 0.3 \times 0.5
\]

---

## Data Sheet (Key Parameters)

| Category | Parameter | Value | Source |
|-----------|------------|--------|--------|
| **Solar PV** | Installed capacity | 1,080 kWp (560 field + 520 roof) | Project data |
|  | Annual measured production | ~260 MWh (2022, incomplete) | Project data |
|  | Monthly capacity factors | 0.036–0.176 (Jan–Dec) | PVGIS (2025 proj.) |
| **Wind** | Installed capacity | ~100 kW (2 × 45–50 kW) | Project data |
|  | Annual expected production | ~80 MWh/yr | Project data |
|  | Monthly capacity factors | 0.114–0.313 (Jan–Dec) | Renewable Ninja (2024) |
| **Electrolyzer** | Rated capacity | 70 kW | Project data |
|  | Baseline operation | 8 h/day × weekdays ≈ 2,080 h/yr | Assumed |
|  | Custom operation | 1–24 h/day (user slider) | Dashboard input |
|  | Specific energy consumption | 48–52.5 kWh/kg H₂ | Literature |
|  | Hydrogen efficiency (LHV) | 64–69 % | Derived |
| **Hydrogen Demand** | Annual demand (5 houses) | 4,922 kg/yr | Facility data |
|  | Monthly distribution | 0.013–0.197 (frac.) | Facility data |
| **Battery** | Type & capacity | 1.4 MWh LFP (≈ 4 stacks) | Project data |
|  | Charge/discharge efficiency | 95 % / 95 % | Project data |
| **Grid** | CO₂ factor | 0.388 kg CO₂/kWh | CBS/PBL (2024) |
| **Heat Recovery** | Fraction recoverable | 20 % of EL input | Literature (Van der Roest 2023) |
| **Buildings** | Areas | 230–597 m² (5 houses) | Case study |
|  | Benchmark demand (A-rated) | 75 kWh/m²/yr (~79 with boiler eff.) | Dutch EPC |
|  | Boiler efficiency | 95 % | Literature |

---

*End of file • October 2025*
