# app.py

import math
import streamlit as st

st.set_page_config(page_title="Van Slyke Cheese Calculator", layout="wide")

st.title("Van Slyke Cheese Yield Calculator")
st.caption("Enter what you know; the app computes any other unknowns it can.")

# Helper math (all % on a 0–100 basis)

def safe_div(a, b):
    return None if b is None or b == 0 else a / b

def calc_fdb(fat_cheese_pct, total_solids_cheese_pct):
    # FDB% = (%fat / %total solids) * 100
    if fat_cheese_pct is None or total_solids_cheese_pct is None or total_solids_cheese_pct == 0:
        return None
    return (fat_cheese_pct / total_solids_cheese_pct) * 100.0

def calc_rs_from_cheese_comp(fat_cheese_pct, casein_cheese_pct, total_solids_cheese_pct):
    # RS = 1 + (TS - fat - casein) / (fat + casein)
    if None in (fat_cheese_pct, casein_cheese_pct, total_solids_cheese_pct):
        return None
    denom = fat_cheese_pct + casein_cheese_pct
    if denom == 0:
        return None
    serum_solids = total_solids_cheese_pct - fat_cheese_pct - casein_cheese_pct
    return 1 + (serum_solids / denom)

def calc_rf_from_pounds(fat_cheese_pct, lbs_cheese, fat_milk_pct, lbs_milk):
    # RF = (%fat in cheese * lbs cheese) / (%fat in milk * lbs milk)
    if None in (fat_cheese_pct, lbs_cheese, fat_milk_pct, lbs_milk):
        return None
    denom = fat_milk_pct * lbs_milk
    if denom == 0:
        return None
    return (fat_cheese_pct * lbs_cheese) / denom

def calc_yield_pct(rf, rc, rs, fat_milk_pct, casein_milk_pct, total_solids_cheese_pct):
    # %Yield = ((RF*F) + (RC*C)) * RS / (TS/100)
    if None in (rf, rc, rs, fat_milk_pct, casein_milk_pct, total_solids_cheese_pct):
        return None
    if total_solids_cheese_pct == 0:
        return None

    ts_frac = total_solids_cheese_pct / 100.0
    return (((rf * fat_milk_pct) + (rc * casein_milk_pct)) * rs) / ts_frac


def calc_lbs_cheese_from_yield(lbs_milk, yield_pct):
    # lbs cheese = lbs milk * (%yield/100)
    if None in (lbs_milk, yield_pct):
        return None
    return lbs_milk * (yield_pct / 100.0)

def calc_yield_pct_from_pounds(lbs_cheese, lbs_milk):
    # %yield = lbs cheese / lbs milk * 100
    if None in (lbs_cheese, lbs_milk) or lbs_milk == 0:
        return None
    return (lbs_cheese / lbs_milk) * 100.0

def solve_rf_from_fdb(fdb_pct, rs, rc, fat_milk_pct, casein_milk_pct):
    """
    Book Eq. 10:
      FDB = (RF*F) / ((RF*F + RC*C) * RS)

    Solve for RF:
      RF = (FDB*RS*RC*C) / (F * (1 - FDB*RS))

    Inputs:
      fdb_pct: FDB in percent (e.g., 52.7)
      rs: RS (e.g., 1.10)
      rc: RC (e.g., 0.95)
      fat_milk_pct: % fat in milk (e.g., 3.7)
      casein_milk_pct: % casein in milk (e.g., 2.5)
    Returns:
      RF (unitless)
    """
    if None in (fdb_pct, rs, rc, fat_milk_pct, casein_milk_pct):
        return None
    if rs == 0 or fat_milk_pct == 0:
        return None

    fdb = fdb_pct / 100.0  # percent -> fraction
    denom = fat_milk_pct * (1 - fdb * rs)
    if denom == 0:
        return None

    return (fdb * rs * rc * casein_milk_pct) / denom

def solve_casein_milk_from_fdb(fdb_pct, rs, rf, rc, fat_milk_pct):
    """
    From:
      FDB% = (RF*F)/(RF*F + RC*C) * RS * 100

    Let y = FDB%/(100*RS)
      y = (RF*F)/(RF*F + RC*C)
      => RC*C = (RF*F) * (1 - y)/y
      => C = (RF*F) * (1 - y)/(y*RC)
    """
    if None in (fdb_pct, rs, rf, rc, fat_milk_pct):
        return None
    if rc == 0 or rs == 0:
        return None

    y = fdb_pct / (100.0 * rs)
    if y <= 0 or y >= 1:
        return None

    return (rf * fat_milk_pct) * ((1 - y) / (y * rc))


def calc_casein_fat_ratio_from_fdb_recoveries(fdb_pct, rf, rc, rs):
    if None in (fdb_pct, rf, rc, rs) or rc == 0 or rs == 0:
        return None
    fdb = fdb_pct / 100.0  # percent -> fraction
    if fdb <= 0:
        return None
    return (rf / rc) * ((1 / (fdb * rs)) - 1)

def calc_casein_from_protein_milk(protein_milk_pct):
    if protein_milk_pct is None:
        return None
    return protein_milk_pct * 0.82


def calc_casein_pct_from_ratio_and_fat(ratio_cf, milk_fat_pct):
    if ratio_cf is None or milk_fat_pct is None:
        return None
    return ratio_cf * milk_fat_pct

def solve_rs_from_yield(yield_pct, rf, rc, fat_milk_pct, casein_milk_pct, total_solids_cheese_pct):
    # RS = Yield% * (TS/100) / ((RF*F) + (RC*C))
    if None in (yield_pct, rf, rc, fat_milk_pct, casein_milk_pct, total_solids_cheese_pct):
        return None
    denom = (rf * fat_milk_pct) + (rc * casein_milk_pct)
    if denom == 0:
        return None
    ts_frac = total_solids_cheese_pct / 100.0
    return (yield_pct * ts_frac) / denom

def calc_fdb_from_milk_recoveries(rf, rc, rs, fat_milk_pct, casein_milk_pct):
    """
    FDB (fraction) = (RF*F) / ((RF*F + RC*C) * RS)
    Returns fraction (0–1). Multiply by 100 for percent.
    """
    if None in (rf, rc, rs, fat_milk_pct, casein_milk_pct):
        return None
    denom = ((rf * fat_milk_pct) + (rc * casein_milk_pct)) * rs
    if denom == 0:
        return None
    return (rf * fat_milk_pct) / denom

def calc_casein_cheese_pct_from_milk(lbs_milk, lbs_cheese, rc, casein_milk_pct):
    """
    Casein in cheese (%) from milk casein balance:
      lbs_casein_in_cheese = RC * (casein_milk% * lbs_milk / 100)
      casein_cheese% = (lbs_casein_in_cheese / lbs_cheese) * 100
    """
    if None in (lbs_milk, lbs_cheese, rc, casein_milk_pct) or lbs_cheese == 0:
        return None
    lbs_casein_in_cheese = rc * (casein_milk_pct * lbs_milk / 100.0)
    return (lbs_casein_in_cheese / lbs_cheese) * 100.0


# UI Inputs
with st.sidebar:
    st.header("Inputs")
    st.caption("Check what you know. Leave unchecked to keep blank.")

    # ----------------
    # Milk
    # ----------------
    with st.expander("Milk", expanded=True):
        c1, c2 = st.columns(2)
        fat_milk = None
        with c1:
            if st.checkbox("Fat in milk (%)", value=False):
                fat_milk = st.number_input("Milk fat (%)", min_value=0.0, step=0.1, format="%.3f")

        protein_milk_pct = None
        with c2:
            if st.checkbox("Protein in milk (%)", value=False):
                protein_milk_pct = st.number_input("Milk protein (%)", min_value=0.0, step=0.1, format="%.3f")

        casein_milk = None
        if st.checkbox("Casein in milk (%)", value=False):
            casein_milk = st.number_input("Milk casein (%)", min_value=0.0, step=0.1, format="%.3f")
        else:
            if protein_milk_pct is not None:
                casein_milk = calc_casein_from_protein_milk(protein_milk_pct)

        if protein_milk_pct is not None and casein_milk is not None:
            st.caption(f"Using casein = 0.82 × protein → **{casein_milk:.3f}% casein**")

        lbs_milk = None
        if st.checkbox("Pounds of milk", value=False):
            lbs_milk = st.number_input("Pounds of milk", min_value=0.0, step=100.0, format="%.2f")

    # ----------------
    # Cheese composition
    # ----------------
    with st.expander("Cheese composition", expanded=True):
        c1, c2 = st.columns(2)

        fat_cheese = None
        with c1:
            if st.checkbox("Fat in cheese (%)", value=False):
                fat_cheese = st.number_input("Cheese fat (%)", min_value=0.0, step=0.1, format="%.3f")

        total_solids_cheese = None
        with c2:
            if st.checkbox("Total solids in cheese (%)", value=False):
                total_solids_cheese = st.number_input("Cheese total solids (%)", min_value=0.0, step=0.1, format="%.3f")

        # Optional moisture input (prevents TS/moisture confusion)
        moisture_cheese = None
        if st.checkbox("Moisture in cheese (%)", value=False):
            moisture_cheese = st.number_input("Cheese moisture (%)", min_value=0.0, step=0.1, format="%.3f")

        # If TS not entered but moisture is, compute TS
        if total_solids_cheese is None and moisture_cheese is not None:
            total_solids_cheese = 100.0 - moisture_cheese
            st.caption(f"Computed total solids = 100 − moisture → **{total_solids_cheese:.3f}%**")

        # Guardrail warning (common error)
        if total_solids_cheese is not None and total_solids_cheese < 30:
            st.warning("Total solids looks very low (<30%). Did you enter moisture? (TS = 100 − moisture)")

        c1, c2 = st.columns(2)
        casein_cheese = None
        with c1:
            if st.checkbox("Casein in cheese (%)", value=False):
                casein_cheese = st.number_input("Cheese casein (%)", min_value=0.0, step=0.1, format="%.3f")

        protein_cheese = None
        with c2:
            if st.checkbox("Protein in cheese (%)", value=False):
                protein_cheese = st.number_input("Cheese protein (%)", min_value=0.0, step=0.1, format="%.3f")

    # ----------------
    # Pounds / Yield
    # ----------------
    with st.expander("Pounds / Yield (optional)", expanded=False):
        lbs_cheese = None
        if st.checkbox("Pounds of cheese", value=False):
            lbs_cheese = st.number_input("Pounds of cheese", min_value=0.0, step=10.0, format="%.2f")

    # ----------------
    # Recovery factors
    # ----------------
    with st.expander("Recovery factors", expanded=True):
        c1, c2 = st.columns(2)

        rc = None
        with c1:
            if st.checkbox("RC (casein recovery)", value=False):
                rc = st.number_input("RC", min_value=0.0, step=0.01, format="%.3f")

        rf_input = None
        with c2:
            if st.checkbox("RF (fat recovery)", value=False):
                rf_input = st.number_input("RF", min_value=0.0, step=0.01, format="%.3f")

        rs_input = None
        if st.checkbox("RS (serum solids factor)", value=False):
            rs_input = st.number_input("RS", min_value=0.0, step=0.01, format="%.3f")

    # ----------------
    # FDB target
    # ----------------
    with st.expander("FDB target (optional)", expanded=False):
        use_fdb_target = st.checkbox("I have a desired/known FDB%", value=False)
        fdb_target = None
        if use_fdb_target:
            fdb_target = st.number_input("FDB (fat in dry basis) %", min_value=0.0, step=0.001, format="%.4f")

# ----------------------------
# Compute what we can
# ----------------------------
# Always can compute FDB from cheese comp (if fat + total solids given)
fdb_from_comp = calc_fdb(fat_cheese, total_solids_cheese)


# RF: either user-provided, or computed from pounds (if lbs known), or solvable from FDB target (if provided + RS)
rf_calc = rf_input

rf_from_pounds = (
    calc_rf_from_pounds(fat_cheese, lbs_cheese, fat_milk, lbs_milk)
    if (lbs_cheese is not None and lbs_milk is not None and fat_cheese is not None and fat_milk is not None)
    else None
)

# RS: use entered casein in cheese if provided, else use computed casein_cheese_calc
rs_calc = rs_input if rs_input is not None else calc_rs_from_cheese_comp(
    fat_cheese, casein_cheese_calc, total_solids_cheese
)

# If still no RF, try solving from an FDB target (or from cheese composition FDB) if user wants that
rf_from_fdb = None
if rf_calc is None and use_fdb_target and fdb_target is not None and rs_calc is not None:
    rf_from_fdb = solve_rf_from_fdb(fdb_target, rs_calc, rc, fat_milk, casein_milk)
    rf_calc = rf_from_fdb
    
fdb_from_milk_frac = calc_fdb_from_milk_recoveries(rf_calc, rc, rs_calc, fat_milk, casein_milk)
fdb_from_milk_pct = None if fdb_from_milk_frac is None else (fdb_from_milk_frac * 100.0)

# Yield
yield_pct = calc_yield_pct(rf_calc, rc, rs_calc, fat_milk, casein_milk, total_solids_cheese)

# Pounds cheese predicted
lbs_cheese_pred = (
    calc_lbs_cheese_from_yield(lbs_milk, yield_pct)
    if (lbs_milk is not None and yield_pct is not None)
    else None
)

# Actual yield from pounds
yield_pct_actual = (
    calc_yield_pct_from_pounds(lbs_cheese, lbs_milk)
    if (lbs_cheese is not None and lbs_milk is not None)
    else None
)

# Try solving RS from actual yield (book method) if RS not provided and not computable from cheese casein
rs_from_yield = None
if rs_input is None and rs_calc is None and yield_pct_actual is not None:
    # Prefer RF from pounds if available, otherwise use rf_calc
    rf_for_rs = rf_from_pounds if rf_from_pounds is not None else rf_calc
    rs_from_yield = solve_rs_from_yield(
        yield_pct_actual, rf_for_rs, rc, fat_milk, casein_milk, total_solids_cheese
    )
    rs_calc = rs_from_yield


# If user has FDB target and RF + others known, solve for required casein in milk (how to standardize)
casein_milk_needed = None
if use_fdb_target and fdb_target is not None and rs_calc is not None and rf_calc is not None:
    casein_milk_needed = solve_casein_milk_from_fdb(fdb_target, rs_calc, rf_calc, rc, fat_milk)
    
ratio_cf = None
if use_fdb_target and fdb_target is not None:
    ratio_cf = calc_casein_fat_ratio_from_fdb_recoveries(fdb_target, rf_calc, rc, rs_calc)

# Choose a cheese weight to use for composition: actual if given, else predicted
lbs_cheese_for_comp = lbs_cheese if lbs_cheese is not None else lbs_cheese_pred

# If user didn't enter casein in cheese, try to compute it from RC + milk casein + pounds
casein_cheese_calc = casein_cheese
if casein_cheese_calc is None:
    casein_cheese_calc = calc_casein_cheese_pct_from_milk(
        lbs_milk, lbs_cheese_for_comp, rc, casein_milk
    )
    
# RS: use entered casein in cheese if provided, else use computed casein_cheese_calc
rs_calc = rs_input if rs_input is not None else calc_rs_from_cheese_comp(
    fat_cheese, casein_cheese_calc, total_solids_cheese
)

# Display
st.subheader("Results")

k1, k2, k3, k4 = st.columns(4)
k1.metric("VS Yield (%)", "—" if yield_pct is None else f"{yield_pct:.2f}")
k2.metric("RF", "—" if rf_calc is None else f"{rf_calc:.3f}")
k3.metric("RS", "—" if rs_calc is None else f"{rs_calc:.3f}")
k4.metric("FDB (%)", "—" if fdb_from_comp is None else f"{fdb_from_comp:.2f}")

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Details")

    if lbs_cheese_pred is not None:
        st.metric("Cheese lbs (predicted)", f"{lbs_cheese_pred:.2f}")

    if yield_pct_actual is not None:
        st.metric("Yield (%) from pounds", f"{yield_pct_actual:.2f}")

    st.metric("Casein in cheese (%)", "—" if casein_cheese_calc is None else f"{casein_cheese_calc:.2f}")

with right:
    st.subheader("Checks / solves")

    if rf_from_pounds is not None:
        st.write(f"RF from pounds (fat balance): **{rf_from_pounds:.3f}**")

    if rf_from_fdb is not None:
        st.write(f"RF from FDB target + RS: **{rf_from_fdb:.3f}**")

    if casein_milk_needed is not None:
        st.write("To hit the entered FDB (holding milk fat fixed):")
        st.write(f"Required **milk casein ≈ {casein_milk_needed:.3f}%**")

    if ratio_cf is not None:
        st.write(f"Required **casein:fat ratio (C/F)**: **{ratio_cf:.3f}**")

    if fdb_from_milk_pct is not None:
        st.write(f"FDB (from milk + RF/RC/RS) ≈ **{fdb_from_milk_pct:.2f}%**")

st.divider()

# Inputs used (trust-builder)
with st.expander("Inputs used (what the calculator actually used)", expanded=False):
    st.write({
        "Milk fat (%)": fat_milk,
        "Milk protein (%)": protein_milk_pct,
        "Milk casein (%)": casein_milk,
        "Milk lbs": lbs_milk,
        "Cheese fat (%)": fat_cheese,
        "Cheese total solids (%)": total_solids_cheese,
        "Cheese casein (%) (entered)": casein_cheese,
        "Cheese protein (%) (entered)": protein_cheese,
        "Cheese lbs": lbs_cheese,
        "RC": rc,
        "RF (used)": rf_calc,
        "RS (used)": rs_calc,
        "FDB target (%)": fdb_target,
    })

# What’s missing (cleaner)
missing = []
if rc is None:
    missing.append("RC")
if rf_calc is None:
    missing.append("RF (enter RF, compute from pounds, or solve from FDB target + RS)")
if rs_calc is None:
    missing.append("RS (enter RS or provide cheese comp to compute)")
if total_solids_cheese is None:
    missing.append("Cheese total solids (or moisture)")

if missing:
    st.warning("Some outputs could not be computed. Missing:\n\n- " + "\n- ".join(missing))
else:
    st.success("All major outputs were computed from your inputs.")

# How it works (collapsible)
with st.expander("How calculations work", expanded=False):
    st.markdown("""
**Actual yield (from pounds)**  
- % Yield = (lbs cheese / lbs milk) × 100  

**Van Slyke predicted yield**  
- % Yield = [ (RF × milk fat%) + (RC × milk casein%) ] × RS ÷ (TS/100)  

**FDB (fat in dry basis)**  
- FDB% = (cheese fat% / cheese total solids%) × 100  

**RS (serum solids factor)**  
- RS = 1 + (TS − fat − casein) / (fat + casein)  

**Milk casein from milk protein (optional)**  
- milk casein% = 0.82 × milk protein%  
""")
