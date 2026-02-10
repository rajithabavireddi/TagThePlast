import streamlit as st
import pandas as pd
import uuid
import os
from datetime import datetime
from PIL import Image
import random

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="TagThePlast", page_icon="♻️", layout="centered")

# ----------------------------
# SESSION STATE
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "customer_batches" not in st.session_state:
    st.session_state.customer_batches = []

# ----------------------------
# DATA SETUP
# ----------------------------
DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=[
        "BatchID", "PlasticType", "Weight", "Quality",
        "Carbon_Saved", "Discount", "Coupon", "Date"
    ])
    df.to_csv(DATA_FILE, index=False)

df = pd.read_csv(DATA_FILE)

# ----------------------------
# PLASTIC FACTORS
# ----------------------------
plastic_factor = {
    "PET": 1.6,
    "HDPE": 1.2,
    "PVC": 1.1,
    "LDPE": 1.3,
    "PP": 1.4,
    "PS": 1.0,
    "Others": 1.2
}

# ----------------------------
# WORKER CREDENTIALS
# ----------------------------
VALID_WORKERS = [
    "sravanthi001@gmail.com",
    "pravallika002@gmail.com",
    "rajitha003@gmail.com",
    "vaishnavim004@gmail.com",
    "vaishnavip005@gmail.com"
]

# ----------------------------
# DISCOUNT LOGIC
# ----------------------------
def calculate_discount(weight, quality):
    base = 10 if quality == "High" else 6
    if weight <= 1:
        return base
    elif weight <= 5:
        return round(base * 1.5, 1)
    elif weight <= 10:
        return round(base * 2, 1)
    else:
        return 25 if quality == "High" else 22

# ----------------------------
# HARD RESET FUNCTION
# ----------------------------
def full_worker_reset():
    st.session_state.customer_batches = []
    for key in list(st.session_state.keys()):
        if key.endswith("_w") or key.endswith("_q") or key.startswith("Select") or key in ["selected_plastics", "discount_category", "brand"]:
            del st.session_state[key]

# ----------------------------
# MOCK DETECTION FUNCTIONS
# ----------------------------
def detect_plastic_type(image):
    return random.choice(list(plastic_factor.keys()))

def detect_quality(image):
    return random.choice(["High", "Low"])

# ============================
# LANDING PAGE
# ============================
if st.session_state.page == "landing":
    st.markdown("<h1 style='text-align:center'>♻️ TagThePlast</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center'>A data-driven incentive system for traceable recycling</h3>", unsafe_allow_html=True)
    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("🧑‍🏭 Worker Login"):
        st.session_state.page = "worker_login"
    if col2.button("👥 Customer View"):
        st.session_state.page = "customer"

# ============================
# WORKER LOGIN
# ============================
elif st.session_state.page == "worker_login":
    st.markdown("<h2 style='text-align:center;'>Worker Login</h2>", unsafe_allow_html=True)
    email = st.text_input("Worker Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email.lower() in VALID_WORKERS:
            st.session_state.page = "worker"
        else:
            st.error("Unauthorized worker")
    if st.button("⬅ Back"):
        st.session_state.page = "landing"

# ============================
# WORKER PANEL
# ============================
elif st.session_state.page == "worker":
    st.markdown("<h2 style='text-align:center;'>Worker Verification Panel</h2>", unsafe_allow_html=True)

    discount_category = st.selectbox(
        "Select Discount Category",
        ["Select", "Medical Discount", "Shopping Discount"],
        key="discount_category"
    )

    brand_selected = False
    if discount_category == "Medical Discount":
        brand = st.selectbox("Select Medical Brand", ["Apollo Pharmacy"], key="brand")
        brand_selected = True
    elif discount_category == "Shopping Discount":
        brand = st.selectbox("Select Shopping Brand", ["Max Fashion"], key="brand")
        brand_selected = True

    if brand_selected:
        # -------------------------------
        # MANUAL PLASTIC TYPE SELECTION (Optional Backup)
        # -------------------------------
        selected_plastics = st.multiselect(
            "Select Plastic Types (Optional Backup)",
            list(plastic_factor.keys()),
            key="selected_plastics"
        )

        # -------------------------------
        # DRAG & DROP IMAGE UPLOADER
        # -------------------------------
        st.markdown("### Or Upload Plastic Images")
        uploaded_files = st.file_uploader(
            "Drag & drop plastic images here",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if st.button("Generate Batch Passport"):
            if not selected_plastics and not uploaded_files:
                st.warning("Select plastic type or upload images to generate batch.")
            else:
                coupon_id = f"TP-{uuid.uuid4().hex[:6].upper()}"
                date_now = datetime.now().strftime("%d %b %Y")
                plastic_inputs = {}

                # PROCESS SELECTED PLASTIC TYPES
                for plastic in selected_plastics:
                    weight = st.number_input(
                        f"Enter Weight (kg) for {plastic}",
                        min_value=0.1,
                        step=0.1,
                        key=f"{plastic}_w"
                    )
                    quality = st.radio(
                        f"Select Quality for {plastic}",
                        ["High", "Low"],
                        key=f"{plastic}_q"
                    )
                    plastic_inputs[plastic] = (plastic, weight, quality)

                # PROCESS UPLOADED IMAGES
                for file in uploaded_files:
                    image = Image.open(file)
                    st.image(image, caption=file.name, width=150)
                    ptype = detect_plastic_type(image)
                    qual = detect_quality(image)
                    weight = st.number_input(
                        f"Enter Weight (kg) for {file.name}",
                        min_value=0.1,
                        step=0.1,
                        key=f"{file.name}_w"
                    )
                    plastic_inputs[file.name] = (ptype, weight, qual)

                # SAVE ALL TO SESSION & CSV
                for key, value in plastic_inputs.items():
                    ptype, w, q = value
                    row = {
                        "BatchID": uuid.uuid4().hex[:8],
                        "PlasticType": ptype,
                        "Weight": w,
                        "Quality": q,
                        "Carbon_Saved": round(w * plastic_factor[ptype], 2),
                        "Discount": calculate_discount(w, q),
                        "Coupon": coupon_id,
                        "Date": date_now
                    }
                    st.session_state.customer_batches.append(row)
                    df.loc[len(df)] = row

                df.to_csv(DATA_FILE, index=False)
                st.success(f"Batch Passport Generated Successfully. Coupon: {coupon_id}")

    # DASHBOARD / SUMMARY
    if st.session_state.customer_batches:
        dashboard_df = pd.DataFrame(st.session_state.customer_batches)
        st.dataframe(dashboard_df)

        total_weight = round(dashboard_df["Weight"].sum(), 2)
        total_carbon = round(dashboard_df["Carbon_Saved"].sum(), 2)
        avg_discount = round(dashboard_df["Discount"].sum() / len(dashboard_df), 2)
        coupon_id = dashboard_df["Coupon"].iloc[0]

        st.markdown(
            f"""
            <div style="border:2px dashed green; padding:15px;">
                <h3>🎟️ Official Recycling Coupon</h3>
                <p><b>Coupon ID:</b> {coupon_id}</p>
                <p><b>Total Plastic:</b> {total_weight} kg</p>
                <p><b>Total Carbon Saved:</b> {total_carbon} kg CO₂</p>
                <p><b>Average Discount:</b> {avg_discount}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # FULL RESET
    if st.button("🔄 Reset Entry"):
        full_worker_reset()
        st.rerun()

    if st.button("Logout"):
        full_worker_reset()
        st.session_state.page = "landing"

# ============================
# CUSTOMER VIEW
# ============================
elif st.session_state.page == "customer":
    st.title("🌱 Your Recycling Benefits")

    discount_rate = {"High": 10, "Low": 5}

    # Display plastic benefit boxes
    for p in plastic_factor:
        st.markdown(f"### {p}")
        cols = st.columns(3)
        idx = 0
        for q in ["High", "Low"]:
            for w in [1, 5, 10]:
                carbon_saved = round(plastic_factor[p] * w, 2)
                disc = discount_rate[q]
                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div style="border:1px solid #ddd; padding:12px; border-radius:8px;">
                        <b>{w} kg | {q}</b><br>
                        ♻️ {carbon_saved} kg CO₂<br>
                        🎁 {disc}% Discount
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                idx += 1

    st.divider()

    # Average Discount Formula Box
    st.markdown(
        """
        <div style="border:2px white; padding:10px; border-radius:3.5px; background-color:black;">
            <h4>🧮 Average Discount Formula:</h4>
            <p><b>Average Discount = Sum of Discount per Plastic Type ÷ 3</b></p>
        </div>
        <br><br>
        """,
        unsafe_allow_html=True
    )

    # Metrics below the formula box
    st.metric("Total Plastic Collected (kg)", round(df["Weight"].sum(), 2))
    st.metric("Total Carbon Saved (kg CO₂)", round(df["Carbon_Saved"].sum(), 2))
    st.metric("Total Batches Recycled", len(df))

    st.subheader("📊 Carbon Saved Overview")
    if not df.empty:
        plastic_graph = (
            df.groupby("PlasticType", as_index=False)["Carbon_Saved"]
            .sum()
            .set_index("PlasticType")
        )
        st.bar_chart(plastic_graph)
    else:
        dummy_graph = pd.DataFrame(
            {"Carbon_Saved": [1, 2, 3, 4, 5, 2, 3]},
            index=list(plastic_factor.keys())
        )
        st.bar_chart(dummy_graph)

    if st.button("Logout"):
        st.session_state.page = "landing"


