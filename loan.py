import streamlit as st
import math
import pandas as pd
from scipy.optimize import brentq

# ---- EMI Calculation Logic ---- #
def calculate_emi(P, R, N):
    r = R / 12 / 100
    if r == 0:
        return P / N
    emi = P * r * (1 + r) ** N / ((1 + r) ** N - 1)
    return emi

def calculate_principal(E, R, N):
    r = R / 12 / 100
    if r == 0:
        return E * N
    P = E * ((1 + r) ** N - 1) / (r * (1 + r) ** N)
    return P

def calculate_tenure(P, R, E):
    r = R / 12 / 100
    if r == 0:
        return P / E
    try:
        n = math.log(E / (E - P * r)) / math.log(1 + r)
        return n
    except (ValueError, ZeroDivisionError):
        raise ValueError("Unable to calculate tenure. Check your values.")

def calculate_rate(P, N, E):
    def func(r):
        r_monthly = r / 12 / 100
        return P * r_monthly * (1 + r_monthly) ** N / ((1 + r_monthly) ** N - 1) - E

    min_emi = P / N
    if E < min_emi:
        raise ValueError("EMI is too low to cover the loan.")

    try:
        R_solution = brentq(func, 0.01, 50)
        return R_solution
    except ValueError:
        raise ValueError("Could not determine interest rate with given values.")

def generate_schedule(P, R, N):
    N = int(N)
    r = R / 12 / 100
    emi = calculate_emi(P, R, N)
    balance = P
    schedule = []

    for i in range(1, N + 1):
        interest = balance * r
        principal_component = emi - interest
        balance -= principal_component
        balance = max(balance, 0)
        schedule.append({
            "Month": i,
            "EMI": round(emi, 2),
            "Principal": round(principal_component, 2),
            "Interest": round(interest, 2),
            "Balance": round(balance, 2)
        })
    return pd.DataFrame(schedule)

# ---- Streamlit UI ---- #
st.set_page_config(page_title="EMI Calculator", layout="centered")

st.title("📊 EMI Calculator")

st.markdown("Enter any **three** of the four fields below. Leave one blank to calculate it.")

col1, col2 = st.columns(2)

with col1:
    principal = st.text_input("Principal (₹)", placeholder="e.g. 500000")
    interest_rate = st.text_input("Interest Rate (%)", placeholder="e.g. 10.5")
with col2:
    tenure = st.text_input("Tenure (months)", placeholder="e.g. 60")
    emi = st.text_input("EMI (₹)", placeholder="e.g. 12000")

if st.button("Calculate"):
    try:
        P = float(principal) if principal else None
        R = float(interest_rate) if interest_rate else None
        N = float(tenure) if tenure else None
        E = float(emi) if emi else None

        missing = [P, R, N, E].count(None)
        if missing != 1:
            st.error("❗ Please leave exactly one field blank.")
        else:
            if E is None:
                E = calculate_emi(P, R, N)
                st.success(f"Calculated EMI: ₹{E:.2f}")
            elif P is None:
                P = calculate_principal(E, R, N)
                st.success(f"Calculated Principal: ₹{P:.2f}")
            elif N is None:
                N = int(round(calculate_tenure(P, R, E)))
                st.success(f"Calculated Tenure: {N} months")
            elif R is None:
                R = calculate_rate(P, N, E)
                st.success(f"Calculated Interest Rate: {R:.2f}%")

            schedule_df = generate_schedule(P, R, N)
            st.markdown("### 🧾 Repayment Schedule")
            st.dataframe(schedule_df, use_container_width=True)

            csv = schedule_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Schedule as CSV",
                data=csv,
                file_name="emi_schedule.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error: {e}")
