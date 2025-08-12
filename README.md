# 🚗 Vahan — Investor Dashboard (Vehicle Registrations)

An interactive investor-oriented dashboard built with Streamlit to visualize and analyze vehicle registration trends in India from 2020 to 2025, using data scraped from the VAHAN portal.

---

## 📌 Features

- **Dual View Modes**  
  - Vehicle Category-wise (2W, 3W, 4W, etc.)  
  - Manufacturer-wise (e.g., TATA, Mahindra, Hero, etc.)
- **Filters Panel**  
  - Select View Mode  
  - Filter by Category/Manufacturer  
  - Year Range Selection
- **KPIs (Horizontally aligned)**  
  - Total Registrations  
  - YoY Growth  
  - QoQ Growth
- **Charts & Visualizations**  
  - Overall Registrations Trend  
  - Registrations over time by Vehicle Category  
  - Top Categories / Manufacturers in Latest Month  
  - YoY% (Month vs Same Month Last Year)  
  - QoQ% (Quarter vs Previous Quarter)  
- **Gainers & Losers Table**  
  - Top market gainers and losers based on YoY%
- Download / Export filtered data to CSV
- Notes section for investment insights

---

## 📂 Project Structure

```plaintext
vahan_investor_dashboard/
│
├── venv/
│
├── app/
│   └── main.py
│
├── data/
│   ├── manufacturer_wise_data_2020_2025.csv
│   └── vehicle_type_wise_data_2020_2025.csv
│
├── scripts/
│   ├── scrape_vehicle_type_data.py
│   └── scrape_manufacturer_data.py
│
└── README.md
```

---

## ⚙️ Installation
```bash
git clone https://github.com/your-username/vahan-investor-dashboard.git
cd vahan-investeR-dashboard
python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

---

## 📂 requirements.txt
```bash
streamlit
pandas
selenium
plotly
webdriver-manager
```

----

## 🚀 Running the Dashboard
```bash
cd app
streamlit run main.py
```
Then open the provided local URL (usually http://localhost:8501).

---

## 📊 Data Sources  
- **`manufacturer_wise_data_2020_2025.csv`** — Manufacturer-wise registrations by month/year.  
- **`vehicle_type_wise_data_2020_2025.csv`** — Vehicle-type-wise registrations (2W, 3W, 4W).  

_Data is scraped from the **VAHAN Portal** using Selenium scripts in `/scripts`._  

---

## 📈 Sample Insights  
- 📈 **2W registrations** surged by **over 15% QoQ** in mid-2023, surpassing 4W growth.  
- 📉 **3W category** continues to decline YoY.  
- ⚡ Certain **niche EV manufacturers** saw **200%+ YoY growth** after new launches.  

---

## 🙌 Acknowledgements  
- **VAHAN Portal** — Data source  
- **Streamlit** — Dashboard framework  
- **Plotly** — Building interactive web-based visualizations
