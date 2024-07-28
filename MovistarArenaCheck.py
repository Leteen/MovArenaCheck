import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText

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
        artist_element = event.select_one('.artista')
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
        if artist_element:
            artist_text = artist_element.get_text(strip=True)
        else:
            artist_text = "Unknown Artist"



        results.append((date_text, status_text))
    return results

def send_email(subject, body, to_email):
    from_email = "joacoremis@gmail.com"  # Replace with your email
    from_password = "uqto qrut qbmo tzad"  # Google's app password

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, from_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

tab1, tab2 = st.tabs(['Movistar Arena', 'All Access'])

with tab1:
    st.title('Checker de tickets de Movistar Arena')
    refresh_rate = st.number_input('Checkear cada: (segundos)', min_value=1, value=5)
    email_address = st.text_input('Email address to notify:', '')

    if 'running' not in st.session_state:
        st.session_state.running = False

    if 'driver' not in st.session_state:
        st.session_state.driver = None

    if 'events' not in st.session_state:
        st.session_state.events = []

    def start_checking():
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        st.session_state.driver = webdriver.Chrome(options=chrome_options)
        st.session_state.driver.get(URL)
        st.session_state.running = True

        # Get initial events
        st.session_state.events = check_status(st.session_state.driver)
        st.session_state.previous_status = {event[0]: event[1] for event in st.session_state.events}

    def stop_checking():
        st.session_state.running = False
        if st.session_state.driver:
            st.session_state.driver.quit()
            st.session_state.driver = None

    column1, column2 = st.columns(2)
    with column1:
        st.button('Start Checking', on_click=start_checking)
    with column2:
        st.button('Stop Checking', on_click=stop_checking)

    # Add Test Notification button
    if st.button('Send Test Notification'):
        if email_address:
            send_email("Test Notification", "This is a test notification from the ticket checker app.", email_address)
            st.success(f"Test email sent to {email_address}")
        else:
            st.error("Please enter a valid email address.")

    highlight_container = st.empty()
    status_container = st.empty()
    timer_container = st.empty()

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
                
                # Check if the event status changed
                previous_status = st.session_state.previous_status.get(date_text, None)
                if previous_status and previous_status != status_text:
                    subject = f"Tan Bionica {date_text} disponible para comprar YA"
                    body = f"Tickets para Tan Bionica {date_text} cambio de {previous_status} a {status_text}!"
                    send_email(subject, body, email_address)
                    st.session_state.previous_status[date_text] = status_text