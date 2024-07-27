import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import time

# URL of the website to scrape
URL = 'https://www.movistararena.com.ar/show/148a7bae-bb0a-4efa-b4f8-aca6f46beb26'

@st.cache_resource
def get_driver():
    return webdriver.Chrome(
        service=Service(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        ),
        options=options,
    )

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--headless")

st.title('Event Status Checker')

refresh_rate = st.slider('Refresh rate (seconds)', min_value=5, max_value=60, value=10, step=5)

if 'running' not in st.session_state:
    st.session_state.running = False

if 'driver' not in st.session_state:
    st.session_state.driver = None

def check_status(driver):
    driver.refresh()
    time.sleep(5)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
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

def start_checking():
    with st.echo():
        st.session_state.driver = get_driver()
        st.session_state.driver.get(URL)
        st.session_state.running = True

def stop_checking():
    st.session_state.running = False
    if st.session_state.driver:
        st.session_state.driver.quit()
        st.session_state.driver = None

st.button('Start Checking', on_click=start_checking)
st.button('Stop Checking', on_click=stop_checking)

status_container = st.empty()
timer_container = st.empty()
highlight_container = st.empty()

while st.session_state.running:
    for i in range(refresh_rate, 0, -1):
        with timer_container:
            st.write(f"Next check in: {i} seconds")
        time.sleep(1)
    
    statuses = check_status(st.session_state.driver)
    
    with highlight_container:
        st.markdown(f"<h4 style='color: yellow;'>Checked at: {time.ctime()}</h4>", unsafe_allow_html=True)
    time.sleep(1)

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