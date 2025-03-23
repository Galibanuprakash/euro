import streamlit as st
import pandas as pd
import google.generativeai as genai
import math
import bcrypt

# Configure Google Gemini API
GEMINI_API_KEY = "AIzaSyDfFj3gMd7paw5qrRFL1hcSevbQjSSVweI"
genai.configure(api_key=GEMINI_API_KEY)

# Authentication setup
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

users = {
    "admin": {
        "name": "Admin",
        "password": hash_password("admin123")  # Hashed password
    }
}

# Authentication UI
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
    # Load Excel data
    @st.cache_data
    def load_data(uploaded_file):
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name="Main-Data")
            df.columns = df.iloc[0]  # Set first row as column headers
            df = df[1:].reset_index(drop=True)  # Cleaned data
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Convert numeric columns safely, replacing invalid values with NaN
            numeric_cols = ["speed (rpm)", "power (kw)"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            return df.dropna(subset=numeric_cols)  # Drop rows with NaN in essential columns
        return None

    # Streamlit UI
    st.title("Flexible Disc Coupling Finder")

    # File Upload
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df = load_data(uploaded_file)
        st.success("File uploaded successfully!")
    else:
        df = None
        st.warning("Please upload an Excel file to proceed.")

    # User Inputs
    speed = st.number_input("Enter Required Speed (RPM)", min_value=0, step=10)
    torque = st.number_input("Enter Required Torque (kNm) (Leave blank if entering Power)", min_value=0.0, step=0.1, value=None)
    power = st.number_input("Enter Required Power (kW) (Leave blank if entering Torque)", min_value=0.0, step=0.1, value=None)

    # Calculate power if torque is provided
    if torque is not None and torque > 0:
        power = (2 * math.pi * speed * torque) / 60  # Power calculation
        st.write(f"Calculated Power: {power:.2f} kW")

    if st.button("Find Best Coupling") and df is not None:
        if power is not None:
            # Find closest matches for speed and power
            df["speed difference"] = abs(df["speed (rpm)"] - speed)
            df["power difference"] = abs(df["power (kw)"] - power)
            df_sorted = df.sort_values(by=["speed difference", "power difference"]).head(5)  # Get top 5 closest matches
            
            if not df_sorted.empty:
                st.success("Best Matching Couplings:")
                
                # Use Gemini model to refine the best couplings selection
                model = genai.GenerativeModel("gemini-1.5-flash")
                for _, row in df_sorted.iterrows():
                    prompt = f"Find the best coupling based on the following data: Speed: {row['speed (rpm)']} RPM, Power: {row['power (kw)']} kW. Provide refined details."
                    response = model.generate_content(prompt)
                    st.write("Coupling Suggestion:")
                    st.write(row.to_dict())
                    st.write("AI Insights:", response.text)
                    st.markdown("---")
            else:
                st.error("No close matches found for the given Speed and Power.")
        else:
            st.error("Please enter either Torque or Power to proceed.")
