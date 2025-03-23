import streamlit as st
import pandas as pd
import math
import bcrypt
import google.generativeai as genai

# Configure Google Gemini API
GEMINI_API_KEY = "AIzaSyCFbnID7J4KnD-hoveRc37CEx_MV9eXUEk"
genai.configure(api_key=GEMINI_API_KEY)

# Authentication Module
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

users = {
    "admin": {
        "name": "Admin",
        "password": hash_password("admin123")  # Hashed password
    }
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
            st.session_state.authenticated = True
            st.success(f"Welcome {users[username]['name']}!")
            st.rerun()
        else:
            st.error("Username/password is incorrect")
else:
    # Data Loading Module
    @st.cache_data
    def load_data(uploaded_file):
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name="Main-Data")
            df.columns = df.iloc[0]  # Set first row as column headers
            df = df[1:].reset_index(drop=True)  # Cleaned data
            df.columns = df.columns.str.strip().str.lower()
            numeric_cols = ["speed (rpm)", "power (kw)"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df.dropna(subset=numeric_cols)
        return None

    # User Interface Module
    st.title("Flexible Disc Coupling Finder")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df = load_data(uploaded_file)
        st.success("File uploaded successfully!")
    else:
        df = None
        st.warning("Please upload an Excel file to proceed.")

    speed = st.number_input("Enter Required Speed (RPM)", min_value=0, step=10)
    torque = st.number_input("Enter Required Torque (kNm) (Leave blank if entering Power)", min_value=0.0, step=0.1)
    power = st.number_input("Enter Required Power (kW) (Leave blank if entering Torque)", min_value=0.0, step=0.1)

    if torque > 0:
        power = (2 * math.pi * speed * torque) / 60
        st.write(f"Calculated Power: {power:.2f} kW")

    # Coupling Matching Module
    if st.button("Find Best Coupling") and df is not None:
        if power is not None:
            df["speed difference"] = abs(df["speed (rpm)"] - speed)
            df["power difference"] = abs(df["power (kw)"] - power)
            df_sorted = df.sort_values(by=["speed difference", "power difference"]).head(5)  # Get top 5 closest matches
            
            if not df_sorted.empty:
                st.success("Best Matching Couplings:")
                for _, row in df_sorted.iterrows():
                    st.write("Coupling Suggestion:")
                    st.write(row.to_dict())
                    st.markdown("---")
            else:
                st.error("No close matches found for the given Speed and Power.")
        else:
            st.error("Please enter either Torque or Power to proceed.")
