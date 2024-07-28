import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager

# Function to setup ChromeDriver using webdriver-manager
@st.experimental_singleton
def install_chromedriver():
    driver_path = ChromeDriverManager().install()
    return driver_path

# Get the path to the installed ChromeDriver
driver_path = install_chromedriver()

# URL of the website to scrape
URL = 'https://www.movistararena.com.ar/show/148a7bae-bb0a-4efa-b4f8-aca6f46beb26'

# Function to check status
def check_status(driver):
    # Refresh the webpage
    driver.refresh()

    # Wait for the page to load completely
    time.sleep(5)

    # Get the page source and parse it with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Select the elements containing the event information
    events = soup.select('.evento-row')

    results = []
    for event in events:
        date_element = event.select_one('.fecha')
        status_button = event.select_one('button')
        
        if date_element:
            date_text = date_element.get_text(strip=True)
        else:
            date_text = "Unknown Date"
        
        if status_button:
            status_text = status_button.get_text(strip=True)
        else:
            status_text = "Agotado"
        
        results.append((date_text, status_text))
    return results

st.title('Event Status Checker')

refresh_rate = st.slider('Refresh rate (seconds)', min_value=5, max_value=60, value=5, step=5)

if 'running' not in st.session_state:
    st.session_state.running = False

if 'driver' not in st.session_state:
    st.session_state.driver = None

def start_checking():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Use the path to ChromeDriver installed by webdriver-manager
    chrome_service = Service(driver_path)
    st.session_state.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    st.session_state.driver.get(URL)
    st.session_state.running = True

def stop_checking():
    st.session_state.running = False
    if st.session_state.driver:
        st.session_state.driver.quit()
        st.session_state.driver = None

if st.button('Start Checking'):
    start_checking()
if st.button('Stop Checking'):
    stop_checking()

highlight_container = st.empty()
status_container = st.empty()
timer_container = st.empty()

if st.session_state.running:
    while st.session_state.running:
        for i in range(refresh_rate, 0, -1):
            with timer_container:
                st.write(f"Next check in: {i} seconds")
            time.sleep(1)
        
        statuses = check_status(st.session_state.driver)
        
        # Highlight the timestamp
        with highlight_container:
            st.markdown(f"<h4 style='color: red;'>Checked at: {time.ctime()}</h4>", unsafe_allow_html=True)
        time.sleep(1)  # Keep the highlight for a second

        with highlight_container:
            st.markdown(f"<h4>Checked at: {time.ctime()}</h4>", unsafe_allow_html=True)

        with status_container.container():
            for date_text, status_text in statuses:
                color = 'green' if status_text == 'Comprar' else 'red'
                st.markdown(f"""
                    <div style='border: 2px solid {color}; padding: 10px; margin: 5px; border-radius: 5px;'>
                        <span style='color:{color}; font-weight: bold;'>{date_text} - {status_text}</span>
                    </div>
                """, unsafe_allow_html=True)
        st.experimental_rerun()
else:
    st.write("Click 'Start Checking' to begin.")
