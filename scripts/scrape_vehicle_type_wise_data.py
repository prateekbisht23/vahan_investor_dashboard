import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd



URL = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
HEADLESS = False
WAIT_TIMEOUT = 20

def setup_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    return driver


def select_primefaces_dropdown(driver, dropdown_id, option_text):
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    # Click dropdown trigger
    dropdown_trigger = wait.until(EC.element_to_be_clickable((By.ID, dropdown_id)))
    dropdown_trigger.click()

    time.sleep(1)

    # Click desired option
    option = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//li[normalize-space(text())='{option_text}']")
    ))
    option.click()

    time.sleep(1)

    body_elem = wait.until(EC.element_to_be_clickable(
        (By.TAG_NAME, "body")
    ))
    body_elem.click()

    time.sleep(0.5)






# Define category grouping
GROUPS = {
    "4W": [
        "FOUR WHEELER (INVALID CARRIAGE)", "HEAVY GOODS VEHICLE", "HEAVY MOTOR VEHICLE", "HEAVY PASSENGER VEHICLE", "LIGHT GOODS VEHICLE", "LIGHT MOTOR VEHICLE", "LIGHT PASSENGER VEHICLE", "MEDIUM GOODS VEHICLE", "MEDIUM MOTOR VEHICLE", "MEDIUM PASSENGER VEHICLE", "OTHER THAN MENTIONED ABOVE"
    ],
    "3W": ["THREE WHEELER (INVALID CARRIAGE)", "THREE WHEELER(NT)", "THREE WHEELER(T)"],
    "2W": ["TWO WHEELER (INVALID CARRIAGE)", "TWO WHEELER(NT)", "TWO WHEELER(T)"]
}

def scrape_table(driver, year):
    wait = WebDriverWait(driver, 20)

    print(f"\n[{year}] Waiting for table body to load...")
    body_table = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@class='ui-datatable-scrollable-body']//table")
    ))
    print(f"[{year}] Table body found.")

    # Get headers from the month header row (<th> elements inside tr[3])
    print(f"[{year}] Waiting for month header row to load...")

    month_header_cells = wait.until(EC.presence_of_all_elements_located(
        (By.XPATH, '//*[@id="groupingTable_head"]/tr[3]/th')
    ))
    month_headers = [h.text.strip().upper() for h in month_header_cells]

    print(f"[{year}] Raw month headers: {month_headers}")

    # Skip any unwanted columns like TOTAL
    month_headers = [m for m in month_headers if m and m != "TOTAL"]

    print(f"[{year}] Month columns detected: {month_headers}")

    print(f"[{year}] Raw month headers: {month_headers}")




    # Prepare DataFrame to hold all rows
    all_rows = []

    page_num = 1
    while True:
        print(f"[{year}] Scraping page {page_num}...")
        rows = body_table.find_elements(By.XPATH, ".//tbody/tr")
        print(f"[{year}] Found {len(rows)} rows on this page.")

        for idx, row in enumerate(rows, start=1):
            cols = row.find_elements(By.TAG_NAME, "td")
            if not cols or len(cols) < len(month_headers) + 2:
                print(f"[{year}] Row {idx} skipped (invalid column count).")
                continue

            category = cols[1].text.strip().upper()
            month_values = [c.text.strip().replace(",", "") for c in cols[2:-1]]
            month_values = [int(v) if v.isdigit() else 0 for v in month_values]

            all_rows.append([category] + month_values)
            print(f"[{year}] Row {idx} -> {category}: {month_values}")

        # Pagination
        try:
            next_btn = driver.find_element(By.XPATH, "//a[contains(@class,'ui-paginator-next')]")
            if "ui-state-disabled" in next_btn.get_attribute("class"):
                print(f"[{year}] No more pages.")
                break
            else:
                print(f"[{year}] Going to next page...")
                next_btn.click()
                time.sleep(1)
                page_num += 1
        except:
            print(f"[{year}] No pagination button found.")
            break

    print(f"[{year}] Total rows collected: {len(all_rows)}")

    # Create DataFrame
    df = pd.DataFrame(all_rows, columns=["Vehicle Category"] + month_headers)
    print(f"[{year}] DataFrame created with shape {df.shape}")

    # Group into 4W, 3W, 2W
    grouped_data = []
    for label, keywords in GROUPS.items():
        mask = df["Vehicle Category"].apply(lambda x: any(k in x for k in keywords))
        sub_df = df[mask]
        print(f"[{year}] {label} matches: {sub_df.shape[0]} rows")

        if sub_df.empty:
            continue

        sums = sub_df[month_headers].sum()
        for month in month_headers:
            grouped_data.append([label, year, month, int(sums[month])])

    final_df = pd.DataFrame(grouped_data, columns=["Category", "Year", "Month", "Registrations"])
    print(f"[{year}] Grouped DataFrame shape: {final_df.shape}")

    return final_df





def main():
    driver = setup_driver(headless=HEADLESS)
    driver.get(URL)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    # Y-Axis → Vehicle Category
    select_primefaces_dropdown(driver, "yaxisVar", "Vehicle Category")
    print("Set Y-Axis to Vehicle Category")

    time.sleep(2)

    # X-Axis → Month Wise
    select_primefaces_dropdown(driver, "xaxisVar", "Month Wise")
    print("Set X-Axis to Month Wise")

    time.sleep(2)


    master_df = []

    # Loop years 2020-2025
    for year in range(2020, 2026):
        select_primefaces_dropdown(driver, "selectedYear", str(year))
        print(f"Set Year to {year}")

        time.sleep(0.5)

        # Click Refresh
        refresh_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Refresh'] | //input[@value='Refresh']"))
        )

        refresh_button.click()
        time.sleep(2)
        print("Clicked Refresh")

        year_df = scrape_table(driver, year)
        master_df.append(year_df)

        # Wait a bit to see the change
        time.sleep(2)

    

    data_folder = os.path.join(os.path.dirname(__file__), '..', 'data')

    os.makedirs(data_folder, exist_ok=True)

    output_path = os.path.join(data_folder, "vehicle_type_wise_data_2020_2025.csv")


    
    final_df = pd.concat(master_df, ignore_index=True)
    final_df.to_csv(output_path, index=False)


    print("Finished looping years")
    driver.quit()




if __name__ == "__main__":
    main()