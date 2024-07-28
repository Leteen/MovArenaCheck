import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
import threading

# Dictionary of URLs for different artists
ARTIST_URLS = {
    'Tan Bionica': 'https://www.movistararena.com.ar/show/148a7bae-bb0a-4efa-b4f8-aca6f46beb26',
    'Keane': 'https://www.movistararena.com.ar/show/1bdf1f48-eac4-4522-b864-d40225dc1df9'
}

# Function to check status
def check_status(driver, url):
    driver.get(url)
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

        results.append((artist_text, date_text, status_text))
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

def start_checking(refresh_rate, email_address, artists_selected):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    driver = webdriver.Chrome(options=chrome_options)

    # Get initial events
    previous_status = {}
    for artist in artists_selected:
        url = ARTIST_URLS[artist]
        events = check_status(driver, url)
        for event in events:
            artist_text, date_text, status_text = event
            previous_status[f"{artist_text} {date_text}"] = status_text

    st.session_state.running = True

    while st.session_state.running:
        statuses = []
        for artist in artists_selected:
            url = ARTIST_URLS[artist]
            statuses.extend(check_status(driver, url))
        
        # Check and notify for changes
        for artist_text, date_text, status_text in statuses:
            event_key = f"{artist_text} {date_text}"
            previous_status_text = previous_status.get(event_key, None)
            if previous_status_text and previous_status_text != status_text:
                subject = f"{artist_text} {date_text} status changed"
                body = f"The tickets for {artist_text} on {date_text} have changed from {previous_status_text} to {status_text}!"
                send_email(subject, body, email_address)
                previous_status[event_key] = status_text
        
        # Update the status container
        status_container.empty()
        with status_container.container():
            for artist_text, date_text, status_text in statuses:
                color = 'green' if status_text == 'Comprar' else 'red'
                st.markdown(f"""
                    <div style='border: 2px solid {color}; padding: 10px; margin: 5px; border-radius: 5px;'>
                        <span style='color:{color}; font-weight: bold;'>{artist_text} - {date_text} - {status_text}</span>
                    </div>
                """, unsafe_allow_html=True)
        
        time.sleep(refresh_rate)

    driver.quit()

def stop_checking():
    st.session_state.running = False

tab1, tab2 = st.tabs(['Movistar Arena', 'All Access'])

with tab1:
    st.title('Checker de tickets de Movistar Arena')
    artists_selected = st.multiselect('Selecciona los artistas', list(ARTIST_URLS.keys()))

    refresh_rate = st.number_input('Checkear cada: (segundos)', min_value=1, value=5)
    email_address = st.text_input('Email address to notify:', '')

    if 'running' not in st.session_state:
        st.session_state.running = False

    column1, column2 = st.columns(2)
    with column1:
        st.button('Start Checking', on_click=lambda: threading.Thread(target=start_checking, args=(refresh_rate, email_address, artists_selected)).start())
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

    if st.session_state.running:
        selected_artist = st.selectbox('Select Artist to View Events', artists_selected)
        for artist in artists_selected:
            url = ARTIST_URLS[artist]
            statuses = check_status(st.session_state.driver, url)

            with highlight_container:
                st.markdown(f"<h4 style='color: red;'>Checked at: {time.ctime()}</h4>", unsafe_allow_html=True)
            time.sleep(1)  # Keep the highlight for a second

            with highlight_container:
                st.markdown(f"<h4>Checked at: {time.ctime()}</h4>", unsafe_allow_html=True)

            if artist == selected_artist:
                with status_container.container():
                    for artist_text, date_text, status_text in statuses:
                        color = 'green' if status_text == 'Comprar' else 'red'
                        st.markdown(f"""
                            <div style='border: 2px solid {color}; padding: 10px; margin: 5px; border-radius: 5px;'>
                                <span style='color:{color}; font-weight: bold;'>{artist_text} - {date_text} - {status_text}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
        # Ensure the user stops checking when they leave the app
        st.on_session_end(stop_checking)
