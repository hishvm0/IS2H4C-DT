# H4C-DT (Digital Twin)

## Project Structure
- `dashboard/` — Streamlit app (KPIs & scenarios)
  - `app.py` — Main dashboard with system visualization
  - `what_if_calculator.py` — What-if scenario calculator
- `map/` — Mapbox + deck.gl 3D city model
- `docs/` — methods & calculations

## Running the Applications

### Main Dashboard
```bash
cd dashboard
streamlit run app.py
```

### What-If Calculator
Explore "what if" scenarios by modifying energy consumption and adding/removing houses:

```bash
# Linux/Mac
./run_what_if.sh

# Windows
run_what_if.bat

# Or manually
cd dashboard
streamlit run what_if_calculator.py
```

See [WHAT_IF_CALCULATOR.md](WHAT_IF_CALCULATOR.md) for detailed documentation.
