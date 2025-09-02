import streamlit as st
import sqlite3
import re
from transformers import pipeline

# ==============================
#  Setup Hugging Face NER model
# ==============================
@st.cache_resource
def load_ner():
    return pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")

ner = load_ner()

# ==============================
#  Database Setup
# ==============================
def init_db():
    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            disease TEXT,
            status TEXT,
            history TEXT,
            phone TEXT,
            doctor TEXT,
            hospital TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 🔥 Initialize DB on start
init_db()

# ==============================
#  Database Operations
# ==============================
def add_patient(name, disease, status, history, phone, doctor, hospital):
    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO patients (name, disease, status, history, phone, doctor, hospital)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, disease, status, history, phone, doctor, hospital))
    conn.commit()
    conn.close()

def view_patients():
    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute("SELECT * FROM patients")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_patient(patient_id):
    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = c.fetchone()
    if patient:
        c.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()
    conn.close()
    return patient

# ==============================
#  De-identification Function
# ==============================
def deidentify_text(text):
    entities = ner(text)
    masked_text = text

    # Mask detected NER entities
    for ent in sorted(entities, key=lambda x: x['start'], reverse=True):
        label = ent['entity_group']
        replacement = f"[MASK_{label}]"
        masked_text = masked_text[:ent['start']] + replacement + masked_text[ent['end']:]

    # Mask phone numbers (10-digit)
    masked_text = re.sub(r'\b\d{10}\b', '[MASK_PHONE]', masked_text)

    return masked_text

# ==============================
#  Streamlit App
# ==============================
st.set_page_config(page_title="Patient Information & Engagement App", layout="centered")
st.title("🏥 Patient Information & Engagement App")

menu = ["Add Patient", "View Patients", "Delete Patient"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Patient":
    st.subheader("➕ Add New Patient")
    name = st.text_input("Patient Name").strip()
    disease = st.text_input("Disease").strip()
    status = st.selectbox("Status", ["Admitted", "Discharged", "Under Observation"])
    history = st.text_area("Medical History").strip()
    phone = st.text_input("Phone Number").strip()
    doctor = st.text_input("Doctor Name").strip()
    hospital = st.text_input("Hospital Name").strip()

    if st.button("Add Patient"):
        if len(name) > 0 and len(disease) > 0 and len(phone) > 0:
            add_patient(name, disease, status, history, phone, doctor, hospital)
            st.success(f"✅ Patient {name} added successfully!")
        else:
            st.error("⚠️ Please fill at least Name, Disease, and Phone.")

elif choice == "View Patients":
    st.subheader("📋 Patient Records")
    patients = view_patients()
    if patients:
        for patient in patients:
            st.write(f"""
                🆔 {patient[0]}  
                👤 Name: {patient[1]}  
                🩺 Disease: {patient[2]}  
                📊 Status: {patient[3]}  
                📜 History: {patient[4]}  
                📞 Phone: {patient[5]}  
                👨‍⚕️ Doctor: {patient[6]}  
                🏥 Hospital: {patient[7]}  
            """)
    else:
        st.info("No patients found.")

elif choice == "Delete Patient":
    st.subheader("🗑️ Delete Patient")
    patients = view_patients()
    if patients:
        patient_dict = {f"{p[1]} (ID: {p[0]})": p[0] for p in patients}
        selected = st.selectbox("Select Patient", list(patient_dict.keys()))
        patient_id = patient_dict[selected]

        if st.button("Delete Patient"):
            patient = delete_patient(patient_id)
            if patient:
                discharge_summary = (
                    f"Patient {patient[1]} with {patient[2]} was {patient[3]}. "
                    f"Medical History: {patient[4]}"
                )
                st.success(f"✅ Patient {patient[1]} deleted successfully!")

                # De-identify before showing
                masked_summary = deidentify_text(discharge_summary)
                st.subheader("📄 De-identified Discharge Summary")
                st.write(masked_summary)
            else:
                st.error("❌ Patient not found!")
    else:
        st.info("No patients available to delete.")
