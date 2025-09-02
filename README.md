#  Patient Tracker + De-identification App

This project tracks patients and automatically **masks sensitive details** (names, doctors, hospitals, phone numbers) in discharge summaries using a Hugging Face NER model.

##  Features
- Add patients with discharge summaries
- Automatically de-identify PHI (Protected Health Information)
- View records in original or masked form
- Built with **Streamlit + Hugging Face + SQLite**

##  Deployment
1. Fork or clone this repo
2. Push to GitHub
3. Go to [Streamlit Cloud](https://share.streamlit.io/) → New App
4. Select `app.py` as entrypoint
5. Done! 
