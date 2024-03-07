import os
import json
import shutil
import subprocess
import time

import countryflag
import requests
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from lxml import etree, html
from typing import Tuple, List, Union

PROXYSCRAPE_URL = "https://api.proxyscrape.com/v2/"


@st.cache_data(show_spinner=False, ttl=180)
def get_proxyscrape_list(country: str='FR') -> Tuple[bool, Union[List, str]]:
    params = {
        'request': 'displayproxies',
        'protocol': 'socks5',
        'timeout': 1000,
        'anonymity': 'all',
        'country': country,
    }
    try:
        response = requests.get(url=PROXYSCRAPE_URL, params=params, timeout=5)
        response.raise_for_status()
        # convert the response to a list
        response = response.text.strip().split('\r\n')
    except Exception as e:
        return False, str(e)
    else:
        return True, response


@st.cache_resource(show_spinner=False)
def get_flag(country: str):
    return countryflag.getflag([country])


@st.cache_resource(show_spinner=False)
def get_python_version() -> str:
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        version = result.stdout.split()[1]
        return version
    except Exception as e:
        return str(e)


@st.cache_resource(show_spinner=False)
def get_chromium_version() -> str:
    try:
        result = subprocess.run(['chromium', '--version'], capture_output=True, text=True)
        version = result.stdout.split()[1]
        return version
    except Exception as e:
        return str(e)


@st.cache_resource(show_spinner=False)
def get_chromedriver_version() -> str:
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        version = result.stdout.split()[1]
        return version
    except Exception as e:
        return str(e)


@st.cache_resource(show_spinner=False)
def get_logpath() -> str:
    return os.path.join(os.getcwd(), 'selenium.log')


@st.cache_resource(show_spinner=False)
def get_chromedriver_path() -> str:
    return shutil.which('chromedriver')


@st.cache_resource(show_spinner=False)
def get_webdriver_options() -> Options:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=NetworkService")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument('--ignore-certificate-errors')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return options


def get_messages_from_log(logs) -> List:
    messages = list()
    for entry in logs:
        logmsg = json.loads(entry["message"])["message"]
        if logmsg["method"] == "Network.responseReceived": # Filter out HTTP responses
            # check for 200 and 204 status codes
            if logmsg["params"]["response"]["status"] not in [200, 204]:
                messages.append(logmsg)
        elif logmsg["method"] == "Network.responseReceivedExtraInfo":
            if logmsg["params"]["statusCode"] not in [200, 204]:
                messages.append(logmsg)
    if len(messages) == 0:
        return None
    return messages


def prettify_html(html_content) -> str:
    return etree.tostring(html.fromstring(html_content), pretty_print=True).decode('utf-8')


def get_webdriver_service(logpath) -> Service:
    service = Service(
        executable_path=get_chromedriver_path(),
        log_output=logpath,
    )
    return service


def delete_selenium_log(logpath: str):
    if os.path.exists(logpath):
        os.remove(logpath)


def show_selenium_log(logpath: str):
    if os.path.exists(logpath):
        with open(logpath) as f:
            content = f.read()
            st.code(body=content, language='log', line_numbers=True)
    else:
        st.error('No log file found!', icon='🔥')


def run_selenium(logpath: str) -> Tuple[str, List, List, str]:
    name = None
    html_content = None
    with webdriver.Chrome(options=get_webdriver_options(),
                        service=get_webdriver_service(logpath=logpath)) as driver:
        url = "https://messages.google.com/web/authentication"
        xpath = '//mw-qr-code/img'
        try:
            driver.get(url)
            time.sleep(2)
            html_content = driver.page_source
            # Wait for the element to be rendered:
            name = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, '//mw-qr-code/img')))
            lien_image = name.get_attribute('src')
        except Exception as e:
            st.error(body='Selenium Exception occured!', icon='🔥')
            st.text(f'{str(e)}\n' f'{repr(e)}')
        finally:
            performance_log = driver.get_log('performance')
            browser_log = driver.get_log('browser')
    return lien_image


if __name__ == "__main__":
    logpath=get_logpath()
    delete_selenium_log(logpath=logpath)
    st.set_page_config(page_title="Selenium Test", page_icon='🕸️', layout="wide",
                        initial_sidebar_state='collapsed')
    left, middle, right = st.columns([3, 8, 2])
    with middle:
        st.title('Selenium on Streamlit Cloud 🕸️')
        st.markdown('''This app is only a very simple test for **Selenium** running on **Streamlit Cloud** runtime.
            The suggestion for this demo app came from a post on the Streamlit Community Forum.<br>
            <https://discuss.streamlit.io/t/issue-with-selenium-on-a-streamlit-app/11563><br><br>
            This is just a very very simple example and more a proof of concept.
            A link is called and waited for the existence of a specific class to read a specific property.
            If there is no error message, the action was successful. Afterwards the log files are displayed.
            Since the target website has geoip blocking enabled, a proxy is required to bypass this and can be selected optionally.
            If you disable the proxy, the app will usually fail on streamlit cloud to load the page.
            ''', unsafe_allow_html=True)
        st.markdown('---')
        middle_left, middle_middle, middle_right = st.columns([3, 1, 4], gap="small")
        with middle_right:
            st.header('Versions')
            st.text('This is only for debugging purposes.\n'
                    'Checking versions that are installed in this environment:\n\n'
                    f'- Python:        {get_python_version()}\n'
                    f'- Streamlit:     {st.__version__}\n'
                    f'- Selenium:      {webdriver.__version__}\n'
                    f'- Chromedriver:  {get_chromedriver_version()}\n'
                    f'- Chromium:      {get_chromium_version()}')
        st.markdown('---')

        if st.button('Start Selenium run'):
            st.warning('Selenium is running, please wait...', icon='⏳')
            result = run_selenium(logpath=logpath)
            if result is None:
                st.error('There was an error, no result found!', icon='🔥')
            else:
                image_placeholder = st.empty()
                image_placeholder.image(result, width=50, use_column_width='auto')
                st.write(result)
            