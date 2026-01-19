# What-If Energy Calculator

## Overview

The What-If Energy Calculator allows you to explore different scenarios for the hydrogen energy system by:

- **Adding or removing houses** from the building portfolio
- **Modifying energy system parameters** (electrolyzer, PV, wind, battery, storage)
- **Adjusting operating parameters** (hours/day, energy source)
- **Comparing scenarios** side-by-side with the baseline configuration

## Features

### 🏠 House Management
- Add new buildings with custom floor area and H₂ demand
- Remove existing buildings from the portfolio
- Automatic H₂ demand estimation based on floor area
- Support for different building types (Residential, Community centre, Office, Commercial)

### ⚡ Energy System Configuration
- Adjust electrolyzer power capacity (kW)
- Modify PV capacity and allocation factor
- Change wind turbine capacity
- Resize battery storage capacity
- Adjust H₂ buffer storage capacity

### 📊 Performance Analysis
- Side-by-side comparison of baseline vs. what-if scenarios
- Monthly H₂ production vs. demand analysis
- CO₂ emissions and avoidance tracking
- Seasonal coverage percentage
- Waste heat recovery potential
- O₂ reuse at WWTP
- Battery utilization metrics

### 💡 Insights & Recommendations
- Automatic analysis of system balance
- Coverage warnings (under/oversized)
- Sustainability impact assessment
- Portfolio change tracking

## How to Use

### Starting the Calculator

```bash
# From the project root directory
cd dashboard
streamlit run what_if_calculator.py
```

Or use the launcher script:

```bash
# From the project root
./run_what_if.sh
```

### Basic Workflow

1. **Explore the Baseline**
   - The calculator starts with the default system configuration
   - Baseline results are shown on the left side of comparisons

2. **Modify Buildings**
   - Use the sidebar **"House Management"** section
   - Add new buildings with the **"➕ Add New House"** expander
   - Remove buildings using the 🗑️ button on each house card
   - Click **"🔄 Reset to Baseline"** to restore the original portfolio

3. **Adjust Energy System**
   - Open the **"🔧 System Capacity"** expander in the sidebar
   - Modify electrolyzer, PV, wind, battery, or storage capacities
   - Adjust the PV allocation factor (% of PV dedicated to H₂ system)
   - Click **"Apply Energy Changes"** to update the system

4. **Change Operating Parameters**
   - Use the **"⚙️ Operating Parameters"** expander
   - Adjust operating hours per day (1-24 hours)
   - Select energy source (Mix, Wind Only, Solar Only, Grid Only)

5. **Analyze Results**
   - Compare key metrics in the **"📊 Performance Comparison"** section
   - View monthly production/demand in the **"📈 Monthly Analysis"** tabs
   - Review insights and recommendations in the **"💡 Insights"** section

6. **Export Results**
   - Click **"📥 Export What-If Results (CSV)"** to download a comparison table
   - Results include all metrics for both baseline and what-if scenarios

## Example Scenarios

### Scenario 1: Adding New Buildings
**Question:** What happens if we add 3 new residential buildings to the system?

1. Click **"➕ Add New House"** in the sidebar
2. Configure each new building:
   - Name: "New Residential 1", "New Residential 2", etc.
   - Type: Residential
   - Area: 250 m²
   - H₂ Demand: Auto-calculated (~750 kg/yr)
3. Click **"Add House"** for each
4. Review the impact on:
   - Seasonal coverage (likely decreases)
   - Total demand increase
   - CO₂ avoided per house

### Scenario 2: Increasing Renewable Capacity
**Question:** Can we achieve 100% seasonal coverage by increasing wind capacity?

1. Open **"🔧 System Capacity"** expander
2. Increase wind capacity from 100 kW to 200 kW
3. Click **"Apply Energy Changes"**
4. Check if seasonal coverage reaches 100%
5. Review curtailed energy to see if we're overshooting

### Scenario 3: Optimizing Battery Storage
**Question:** What battery size minimizes curtailment while maintaining coverage?

1. Start with current configuration
2. Note baseline curtailed energy
3. Open **"🔧 System Capacity"** expander
4. Try different battery capacities (e.g., 1000, 1500, 2000 kWh)
5. Click **"Apply Energy Changes"** for each
6. Compare curtailment and seasonal coverage
7. Find the sweet spot that balances both

### Scenario 4: Community Centre Expansion
**Question:** What if we convert a residential building to a large community centre?

1. Remove an existing residential building (🗑️ button)
2. Add a new community centre:
   - Name: "Community Hub"
   - Type: Community centre
   - Area: 800 m²
   - H₂ Demand: ~2,400 kg/yr
3. Review the impact on total demand and system balance

## Understanding the Results

### Key Metrics

- **H₂ Demand (kg/yr)**: Total annual hydrogen demand from all buildings
- **H₂ Production (kg/yr)**: Annual hydrogen produced by the electrolyzer
- **Seasonal Coverage (%)**: Percentage of annual demand met by production
  - < 90%: Undersized system
  - 90-110%: Well-balanced system ✓
  - > 110%: Oversized system

- **CO₂ Avoided (kg/yr)**: CO₂ emissions avoided by using green H₂ instead of grid electricity
- **Grid Emissions (kg/yr)**: CO₂ emitted from grid electricity (should be 0 for 100% renewable)

### Color Coding

- **🟢 Green arrows/positive changes**: Improvements (more coverage, more CO₂ avoided)
- **🔴 Red arrows/negative changes**: Reductions (less coverage, more emissions)
- **Baseline badge**: Original system configuration (gray)
- **What-If badge**: Your modified scenario (purple)

### Monthly Analysis

The **"Monthly Balance"** chart shows:
- Blue bars: H₂ production per month
- Red bars: H₂ demand per month
- Production should ideally match or exceed demand in most months

Gaps indicate months where storage or backup is needed.

## Tips & Best Practices

1. **Start Small**: Make one change at a time to understand its isolated impact
2. **Watch Coverage**: Aim for 90-110% seasonal coverage for a well-balanced system
3. **Check Curtailment**: High curtailment means you're wasting renewable energy
4. **Consider Storage**: If coverage is good but monthly imbalances exist, increase storage
5. **Reset Often**: Use the "Reset to Baseline" button to start fresh
6. **Export Results**: Save your scenarios for documentation and reporting

## Technical Details

### Calculation Methodology

The calculator uses the same energy balance model as the main dashboard:
- Monthly renewable generation based on capacity factors
- Weekday-only electrolyzer operation
- Battery charge/discharge with efficiency losses
- Monthly H₂ storage buffering
- Seasonal demand distribution

### Assumptions

- Electrolyzer SEC: 50 kWh/kg H₂
- PV capacity factors: Monthly averages for Netherlands
- Wind capacity factors: Monthly averages for Netherlands
- Battery efficiency: 95% charge/discharge
- A-label heat demand: 75 kWh/m²/year
- H₂ LHV: 33.3 kWh/kg

### Limitations

- Simplified monthly timestep (not hourly)
- Weekday-only operation assumption
- No dynamic electricity pricing
- No inter-seasonal storage modeling
- Heating demand based on reference values, not actual consumption

## Integration with Main Dashboard

The What-If Calculator is a standalone tool but uses the same data and calculation engine as the main dashboard. Future updates will allow:
- Copying what-if scenarios to the main dashboard
- Saving custom scenarios
- Sharing scenario configurations

## Troubleshooting

**Issue**: Seasonal coverage is very low after adding houses
**Solution**: Increase electrolyzer capacity or renewable generation to match higher demand

**Issue**: High curtailment even with battery
**Solution**: Battery may be too small or demand too low. Add more houses or reduce generation.

**Issue**: Changes don't appear after clicking "Apply"
**Solution**: Make sure you clicked the "Apply Energy Changes" button and wait for the page to reload

## Support

For questions or issues, please refer to the main project README or contact the development team.
