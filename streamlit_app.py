import os
import json
import shutil
import subprocess
import time
import streamlit_antd_components as sac
import function
import pandas as pd
import undetected_chromedriver as uc

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

def run_selenium2(logpath: str) -> Tuple[str, List, List, str]:
    name = None
    html_content = None
    with webdriver.Chrome(options=get_webdriver_options(),
                        service=get_webdriver_service(logpath=logpath)) as driver:
        url = "https://messages.google.com/web/authentication"
        xpath = '//mw-qr-code/img'
        try:
            driver = driver
        except Exception as e:
            st.error(body='Selenium Exception occured!', icon='🔥')
            st.text(f'{str(e)}\n' f'{repr(e)}')
    return driver

if __name__ == "__main__":
    logpath=get_logpath()
    delete_selenium_log(logpath=logpath)
    st.set_page_config(page_title="SmartSMS",layout="wide", initial_sidebar_state="auto", page_icon="logo_SmartSMS.png")
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    st.header("SMARTSMS: PERSONNALISEZ ET ENVOYEZ DES SMS EN MASSE FACILEMENT")
    function.load_styles()
    segment =sac.segmented(
        items=[
            sac.SegmentedItem(label='SmartSMS'),
            sac.SegmentedItem(label="Guide d\'utilisation"),
            sac.SegmentedItem(label='Contactez-nous'),
        ], format_func='title', align='center'
    )


    if segment=="SmartSMS":

        z1, z2 = st.columns((11,4))
        with z1:
            st.title(":blue[Choisissez votre fichier de contacts :]")
        with z2:
            contacts = st.file_uploader("", type=["xls", "xlsx"])

        col1=col2=col3=col4=COL1=COL2=COL3=COL4=sim=""
        if contacts is not None:
            #read upload file and creer list from columns
            df = pd.read_excel(contacts)
            columns = set(df.columns)

            b1, b2,b3 = st.columns(3)
            with b1:
                numero = st.selectbox('Sélectionner la colonne des numéros de téléphone:',columns,index=None)
            with b2:
                une_puce = st.selectbox("J'ai uniquement une SIM dans mon smartphone:",["OUI","NON"],index=None)
            if une_puce=="NON":
                with b3:
                    sim = st.selectbox('Veuillez sélectionner la carte SIM à utiliser:',["SIM 1","SIM 2"],index=None)

            a1, a2, a3, a4 = st.columns(4)
            #on crée plusieurs colonnes pour 
            with a1:
                col1 = st.selectbox('1ère info personnelle:',columns,index=None)

            with a2:
                if col1 is not None and col1 != '':
                    col2 = st.selectbox('2nd info personnelle:',columns,index=None)

            with a3:
                if col2 is not None and col2 != '':
                    col3 = st.selectbox('3eme info personnelle:',columns,index=None)

            with a4:
                if col3 is not None and col3 != '':
                    col4 = st.selectbox('4eme info personnelle:',columns,index=None)

            #msg texte
            msg = st.text_area('Entrez votre message')
            validate_msg =st.button("Envoyez les messages")
            messages = []

            if validate_msg:
                #verification de la colonne numero
                if numero not in columns:
                    st.warning("Erreur : Veuillez sélectionner la colonne contenant les contacts avant de continuer. Assurez-vous de sélectionner la bonne colonne pour garantir une saisie correcte des informations.", icon="⚠️")

                elif function.verifier_numeros_telephone(df,numero)!=True:
                    error = function.verifier_numeros_telephone(df,numero)
                    st.warning(f"{error}.", icon="⚠️")

                elif une_puce not in ["OUI","NON"]:
                    st.warning("Erreur : Aucune option sélectionnée. Veuillez nous informer si vous avez uniquement une carte SIM ou non.", icon="⚠️")
                elif (une_puce == "NON") and (sim not in ["SIM 1","SIM 2"]):
                    st.warning("Erreur : Aucune carte SIM sélectionnée. Veuillez choisir une carte SIM et réessayer. Assurez-vous de sélectionner la carte SIM que vous souhaitez utiliser pour l'envoi des SMS.", icon="⚠️")
                 
                elif len(msg)==0:
                    st.warning("Erreur : Aucun message saisi. Veuillez écrire votre message avant de réessayer", icon="⚠️")

                else:
                    sim_number = function.return_sim_number(sim)
                    NUMEROS = df[numero]
                    resultat = function.corriger_msg(msg, col1, col2, col3, col4)
                    msg_corrige = resultat[0]

                    if len(resultat[1])==0:
                        message = msg_corrige.replace('{}','')
                        for i in range(len(df)):
                            messages.append(message)

                    if len(resultat[1])==1:
                        for i in range(len(df)):
                            COL1 = df.loc[i,col1]
                            message = msg_corrige.format(COL1)
                            messages.append(message)

                    if len(resultat[1])==2:
                        for i in range(len(df)):
                            COL1, COL2 = df.loc[i,col1], df.loc[i,col2]
                            message = msg_corrige.format(*[COL1, COL2])
                            messages.append(message)

                    if len(resultat[1])==3:
                        for i in range(len(df)):
                            COL1, COL2,COL3 = df.loc[i,col1], df.loc[i,col2], df.loc[i,col3]
                            message = msg_corrige.format(*[COL1, COL2, COL3])
                            messages.append(message)

                    if len(resultat[1])==4:
                        for i in range(len(df)):
                            COL1, COL2,COL3, COL4 = df.loc[i,col1], df.loc[i,col2], df.loc[i,col3], df.loc[i,col4]
                            message = msg_corrige.format(*[COL1, COL2, COL3, COL4])
                            messages.append(message)

                    #lancement du navigateur
                    #driver = get_driver()
                    #driver =uc.Chrome(options=chrome_options)
                    driver = webdriver.Chrome(options=get_webdriver_options(), service=get_webdriver_service(logpath=logpath))
                    driver.set_window_size(650,750)
                    driver.get("https://messages.google.com/web/authentication")
                    time.sleep(5)

                    #attendre que le qrcode soit disponble
                    wait_element = WebDriverWait(driver, 120)
                    wait_element.until(EC.presence_of_element_located((By.XPATH, '//mw-qr-code/img')))

                    image_placeholder = st.empty()
                    texte_placeholder = st.empty()

                    #recuperation et affichage du code QR de manière actualise en standant le scan
                    try:
                        while True:
                            # Récupération du QR code
                            qrcode = driver.find_element(By.XPATH, '//mw-qr-code/img')
                            lien_image = qrcode.get_attribute('src')

                            texte_placeholder.write(
                                """
                                ### :black[SCANNER LE QR CODE]
                                """
                                )
                            # Afficher l'image dans Streamlit
                            image_placeholder.image(lien_image, width=50, use_column_width='auto')

                            # Attendre 2 secondes avant de mettre à jour le QR code
                            time.sleep(2)

                    #une fois le code QR scanné
                    except:
                        with image_placeholder:
                            st.write('error')
                        with texte_placeholder:
                            st.write('error')

                    time.sleep(2)
                    

        else:
            st.info("Bienvenue dans notre application SmartSMS ! Vous pouvez envoyer des SMS personnalisés en masse. Avant de commencer, veuillez charger un fichier de contacts.", icon="ℹ️")

    if segment=="Guide d\'utilisation":
        st.title(":blue[:one:. Choisissez votre fichier de contacts]")
        st.info(":file_folder: Sur la première page de l'application, vous serez invité à télécharger votre fichier de contacts au format Excel (xlsx ou xls). Assurez-vous que votre fichier contient une colonne de numéros de téléphone aux formats suivants: '+225 XX XX XX XX XX', '225 XX XX XX XX XX' ou 'XX XX XX XX XX'.")

        st.title(":blue[:two:. Configuration des informations de bases]")
        st.info(":wrench: Après avoir téléchargé votre fichier de contacts, vous devrez spécifier les informations obligatoires pour faire fonctionner le programme. Sélectionnez les colonnes correspondantes pour le numéro de téléphone et la carte SIM à utiliser.")

        st.title(":blue[:three:. Configuration des informations personnelles]")
        st.info(":wrench: Après avoir téléchargé votre fichier de contacts, vous devrez spécifier les informations personnelles à inclure dans vos messages. Sélectionnez les colonnes correspondantes, comme par exemple le nom et prénoms.")

        st.title(":blue[:four:. Rédigez votre message]")
        st.info(":memo: Utilisez la zone de texte prévue pour saisir le message que vous souhaitez envoyer. Vous devez utiliser le caractère de substitution '@' pour personnaliser votre message avec les informations de chaque contact. le caractere @ est utilisé a chaque fois qu'on souhaite inclures des informations personnelles, par exemple si on veut avoir le resultat suivant: 'Bonjour monsieur Amany votre matricule est XX001' on devra saisir le texte 'Bonjour monsieur @ votre matricule est @', avec pour colonne selectionnées dans l'odre 'NOM ET PRENOMS' ET 'MATRICULE'")
        st.title(":blue[:five:. Vérifications avant l'envoi]")
        st.info("✅ Avant d'appuyer sur le bouton 'Envoyez les messages', assurez-vous que toutes les étapes précédentes sont correctement configurées. Vérifiez que le numéro de téléphone, la carte SIM, et le message sont corrects.")

        st.title(":blue[:six:. Scannez le code QR]")
        st.info(":old_key: Une fois que vous avez confirmé les détails, cliquez sur le bouton 'Envoyez les messages'. Cela ouvrira une fenêtre avec un code QR que vous devrez scanner à l'aide de l'application Messages de Google sur votre téléphone.")

        st.title(":blue[:seven:. Envoi des SMS]")
        st.info(":arrow_up: Après avoir scanné le code QR, l'application commencera à envoyer les SMS automatiquement. Assurez-vous que votre navigateur reste ouvert pendant tout le processus d'envoi.")

        st.title(":blue[:seven:. Fin de l'opération]")
        st.info(":end: Une fois que tous les messages ont été envoyés avec succès, l'application affichera un message de réussite. Vous pouvez maintenant fermer l'application.")


    left, middle, right = st.columns([3, 8, 2])
    with middle:
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
    

    footer="""<style>
        a:link , a:visited{
        color: blue;
        background-color: transparent;
        text-decoration: underline;
        }

        a:hover,  a:active {
        color: red;
        background-color: transparent;
        text-decoration: underline;
        }

        .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: black;
        text-align: center;
        }
    </style>
    <div class="footer">
        <p>Developed by <a style='display: block; text-align: center;' href="https://www.linkedin.com/in/nsi%C3%A9ni-kouadio-eli%C3%A9zer-amany-613681185" target="_blank">Nsiéni Amany Kouadio</a></p>
    </div>
    """
    st.markdown(footer,unsafe_allow_html=True)