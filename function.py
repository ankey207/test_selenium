# Importation des modules nécessaires
import streamlit as st
import pandas as pd
import re

@st.cache_data
def load_styles():
        with open('style.css') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def verifier_numeros_telephone(dataframe, nom_colonne):   
    # Définir un motif regex pour les numéros de téléphone
    motif_telephone = re.compile(r'^(\+225|\b225)?\d{10}$')

    # Vérifier chaque valeur dans la colonne
    for index, valeur in enumerate(dataframe[nom_colonne]):
        if not motif_telephone.match(str(valeur)):
            return f"Erreur : La valeur à la ligne {index+1} de la colonne '{nom_colonne}' n'est pas un numéro de téléphone valide. Veuillez corriger cette valeur avant de réessayer. Assurez-vous de sélectionner la bonne colonne contenant les contacts, chaque valeur de cette doit être un numéro de téléphone correct."
        else:
            return True

def corriger_msg(texte, col1, col2, col3, col4):
    occurrences = [col for col in [col1, col2, col3, col4] if isinstance(col,str) and len(col)!=0]
    
    for occurence in occurrences:
        if '@' in texte:
            texte = texte.replace('@', str('{}'), 1)

    return texte,occurrences

def return_sim_number(sim):
    if sim == "SIM 1":
        return 0
    elif sim == "SIM 2":
        return 1
    else:
        return None

    #load the style file