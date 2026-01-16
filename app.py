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
    # %Yield = ((RF*%fat_milk) + (RC*%casein_milk)) / %solids_in_cheese  * RS
    if None in (rf, rc, rs, fat_milk_pct, casein_milk_pct, total_solids_cheese_pct):
        return None
    if total_solids_cheese_pct == 0:
        return None
    return (((rf * fat_milk_pct) + (rc * casein_milk_pct)) / total_solids_cheese_pct) * rs

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
    Using:
      FDB% = (RF*F)/(RF*F + RC*C) * RS * 100

    Let y = FDB% / (100*RS).
      RF = (y*RC*C) / (F*(1 - y))
    """
    if None in (fdb_pct, rs, rc, fat_milk_pct, casein_milk_pct):
        return None
    if rs == 0 or fat_milk_pct == 0:
        return None

    y = fdb_pct / (100.0 * rs)
    if y <= 0 or y >= 1:
        return None

    return (y * rc * casein_milk_pct) / (fat_milk_pct * (1 - y))

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

# UI Inputs
with st.sidebar:
    st.header("Inputs you have")
    st.info("Check the boxes for the values you know. Leave others unchecked to keep them blank.")

    # ----------------
    # Milk
    # ----------------
    st.subheader("Milk")

    fat_milk = None
    if st.checkbox("I know % fat in milk", value=False):
        fat_milk = st.number_input("% fat in milk", min_value=0.0, step=0.1, format="%.3f")

    casein_milk = None
    if st.checkbox("I know % casein in milk", value=False):
        casein_milk = st.number_input("% casein in milk", min_value=0.0, step=0.1, format="%.3f")

    lbs_milk = None
    if st.checkbox("I know pounds of milk", value=False):
        lbs_milk = st.number_input("Pounds of milk", min_value=0.0, step=100.0, format="%.2f")

    # ----------------
    # Cheese composition
    # ----------------
    st.subheader("Cheese composition")

    fat_cheese = None
    if st.checkbox("I know % fat in cheese", value=False):
        fat_cheese = st.number_input("% fat in cheese", min_value=0.0, step=0.1, format="%.3f")

    total_solids_cheese = None
    if st.checkbox("I know % total solids in cheese", value=False):
        total_solids_cheese = st.number_input("% total solids in cheese", min_value=0.0, step=0.1, format="%.3f")

    casein_cheese = None
    if st.checkbox("I know % casein in cheese", value=False):
        casein_cheese = st.number_input("% casein in cheese", min_value=0.0, step=0.1, format="%.3f")

    # ----------------
    # Pounds (optional)
    # ----------------
    st.subheader("Pounds / Yield (optional)")

    lbs_cheese = None
    if st.checkbox("I know pounds of cheese", value=False):
        lbs_cheese = st.number_input("Pounds of cheese", min_value=0.0, step=10.0, format="%.2f")

    # ----------------
    # Recovery factors
    # ----------------
    st.subheader("Recovery factors")

    rc = None
    if st.checkbox("I know RC (casein recovery)", value=False):
        rc = st.number_input("RC (casein recovery)", min_value=0.0, step=0.01, format="%.3f")

    rf_input = None
    if st.checkbox("I already know RF", value=False):
        rf_input = st.number_input("RF value", min_value=0.0, step=0.01, format="%.3f")

    rs_input = None
    if st.checkbox("I already know RS", value=False):
        rs_input = st.number_input("RS value", min_value=0.0, step=0.01, format="%.3f")

    # ----------------
    # FDB target (optional)
    # ----------------
    st.subheader("FDB target (optional)")
    use_fdb_target = st.checkbox("I have a desired/known FDB%", value=False)
    fdb_target = None
    if use_fdb_target:
        fdb_target = st.number_input("FDB (fat in dry basis) value", min_value=0.0, step=0.001, format="%.4f")

# ----------------------------
# Compute what we can
# ----------------------------
# Always can compute FDB from cheese comp (if fat + total solids given)
fdb_from_comp = calc_fdb(fat_cheese, total_solids_cheese)

# RS: either user-provided, or computed from cheese composition if casein_cheese provided
rs_calc = rs_input if rs_input is not None else calc_rs_from_cheese_comp(fat_cheese, casein_cheese, total_solids_cheese)

# RF: either user-provided, or computed from pounds (if lbs known), or solvable from FDB target (if provided + RS)
rf_calc = rf_input

rf_from_pounds = (
    calc_rf_from_pounds(fat_cheese, lbs_cheese, fat_milk, lbs_milk)
    if (lbs_cheese is not None and lbs_milk is not None and fat_cheese is not None and fat_milk is not None)
    else None
)

# If still no RF, try solving from an FDB target (or from cheese composition FDB) if user wants that
rf_from_fdb = None
if rf_calc is None and use_fdb_target and fdb_target is not None and rs_calc is not None:
    rf_from_fdb = solve_rf_from_fdb(fdb_target, rs_calc, rc, fat_milk, casein_milk)
    rf_calc = rf_from_fdb

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


# If user has FDB target and RF + others known, solve for required casein in milk (how to standardize)
casein_milk_needed = None
if use_fdb_target and fdb_target is not None and rs_calc is not None and rf_calc is not None:
    casein_milk_needed = solve_casein_milk_from_fdb(fdb_target, rs_calc, rf_calc, rc, fat_milk)
    
ratio_cf = None
if use_fdb_target and fdb_target is not None:
    ratio_cf = calc_casein_fat_ratio_from_fdb_recoveries(fdb_target, rf_calc, rc, rs_calc)

# Display
col1, col2 = st.columns(2)

with col1:
    st.subheader("Computed values")
    st.metric("FDB (from cheese composition)", "—" if fdb_from_comp is None else f"{fdb_from_comp:.2f}%")

    st.metric("RS", "—" if rs_calc is None else f"{rs_calc:.3f}")
    st.metric("RF", "—" if rf_calc is None else f"{rf_calc:.3f}")
    st.metric("% Yield (predicted)", "—" if yield_pct is None else f"{yield_pct:.2f}%")

    if lbs_cheese_pred is not None:
        st.metric("Cheese lbs (predicted from milk lbs)", f"{lbs_cheese_pred:.2f}")

with col2:
    st.subheader("Checks / extra solves")
    if yield_pct_actual is not None:
        st.metric("% Yield (actual from lbs)", f"{yield_pct_actual:.2f}%")

    if rf_from_pounds is not None:
        st.write(f"RF computed from pounds (fat balance): **{rf_from_pounds:.3f}**")

    if rf_from_fdb is not None:
        st.write(f"RF solved from FDB target + RS: **{rf_from_fdb:.3f}**")

    if casein_milk_needed is not None:
        st.write("If you keep milk fat fixed and want the entered FDB,")
        st.write(f"required **% casein in milk ≈ {casein_milk_needed:.3f}%**")

    if ratio_cf is not None:
        st.write(f"Required **casein:fat ratio (C/F)** from FDB: **{ratio_cf:.3f}**")


st.divider()
st.subheader("What’s missing?")
missing = []
if rc is None:
    missing.append("RC (enter RC, casein recovery)")
if rf_calc is None:
    missing.append("RF (need pounds milk + pounds cheese, OR enter RF directly, OR provide FDB target + RS to solve RF)")
if yield_pct is None:
    missing.append("% Yield (need RF, RC, RS, milk fat%, milk casein%, and cheese total solids%)")

if missing:
    st.warning("Some outputs couldn't be computed because these are missing:\n\n- " + "\n- ".join(missing))
else:
    st.success("All major outputs were computed from your inputs.")
    
    st.divider()
st.subheader("How to calculate each value")

st.markdown("""**Cheese yield (% from pounds)**  
You must enter:
- Pounds of milk  
- Pounds of cheese  

---

**Predicted cheese yield (Van Slyke)**  
You must enter:
- % fat in milk  
- % casein in milk  
- % total solids in cheese  
- RC (casein recovery)  
- RS (either enter RS directly **or** provide % fat + % casein + % total solids in cheese)  
- RF (either enter RF directly **or** provide pounds of milk + pounds of cheese **or** provide FDB + RS)

---

**Pounds of cheese (predicted)**  
You must enter:
- Pounds of milk  
- A calculable cheese yield (actual or predicted)

---

**RF (fat recovery)**  
You must enter **one** of the following:
- Pounds of milk + pounds of cheese  
- RF directly  
- FDB + RS + milk composition  

---

**RS (serum solids factor)**  
You must enter **one** of the following:
- RS directly  
- % fat in cheese + % casein in cheese + % total solids in cheese  

---

**FDB (fat in dry basis)**  
You must enter:
- % fat in cheese  
- % total solids in cheese  

---

**Milk casein needed to hit a target FDB**  
You must enter:
- Target FDB  
- RS  
- RF  
- RC  
- % fat in milk  
""")
