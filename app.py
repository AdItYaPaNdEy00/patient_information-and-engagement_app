import sqlite3
import streamlit as st
from transformers import pipeline

# Connect database (creates if not exists)
conn = sqlite3.connect("patients.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    symptoms TEXT,
    discharge_summary TEXT,
    discharge_summary_masked TEXT
)
""")

# Load NER model
@st.cache_resource
def load_model():
    return pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")

ner = load_model()

def deidentify_text(text):
    """Mask sensitive entities"""
    entities = ner(text)
    masked_text = text
    for ent in entities:
        if ent['entity_group'] in ["PATIENT", "DOCTOR", "HOSPITAL", "PHONE"]:
            masked_text = masked_text.replace(ent['word'], "[MASKED]")
    return masked_text

def add_patient(name, symptoms, discharge_summary):
    masked_summary = deidentify_text(discharge_summary)
    cursor.execute(
        "INSERT INTO patients (name, symptoms, discharge_summary, discharge_summary_masked) VALUES (?, ?, ?, ?)",
        (name, symptoms, discharge_summary, masked_summary)
    )
    conn.commit()

# ----------------- STREAMLIT UI -----------------
st.title("🏥 Patient Tracker + De-identification App")

menu = st.sidebar.radio("Menu", ["Add Patient", "View Patients"])

if menu == "Add Patient":
    st.subheader("➕ Add a New Patient")
    name = st.text_input("Patient Name")
    symptoms = st.text_input("Symptoms")
    discharge_summary = st.text_area("Discharge Summary")

    if st.button("Save Patient"):
        if name and discharge_summary:
            add_patient(name, symptoms, discharge_summary)
            st.success("✅ Patient added successfully with de-identification")
        else:
            st.error("⚠ Please fill in required fields")

elif menu == "View Patients":
    st.subheader("📋 Patient Records")
    deid = st.checkbox("Show De-identified Data", value=True)

    if deid:
        cursor.execute("SELECT id, name, symptoms, discharge_summary_masked FROM patients")
    else:
        cursor.execute("SELECT id, name, symptoms, discharge_summary FROM patients")

    patients = cursor.fetchall()

    for p in patients:
        st.write(f"**ID:** {p[0]}")
        st.write(f"**Name:** {p[1]}")
        st.write(f"**Symptoms:** {p[2]}")
        st.write(f"**Discharge Summary:** {p[3]}")
        st.markdown("---")
