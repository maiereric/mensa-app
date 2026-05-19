import requests
import pandas as pd
from bs4 import BeautifulSoup


def mensa_get_html(url):
    """
    Lädt den rohen HTML-Code der angegebenen Mensa-URL herunter.
    """
    r = requests.get(url)
    return r.text


def mensa_get_data(html_content):
    """
    Filtert die Kategorien, Gerichte, Preise, Bewertungen sowie
    Datum, Standort und Theke aus dem HTML.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    meals_list = []

    theken = soup.find_all('div', attrs={'data-type': 'theke-slider'}) # Finde alle "Theken"

    for theke in theken:
        kategorie_tag = theke.find('span', class_='label')
        kategorie = kategorie_tag.text.strip() if kategorie_tag else "Unbekannt" # Kategorie-Namen herausfinden (Da Capo etc.)

        artikel_liste = theke.find_all('article', class_='theke-slider-item') # Alle Gerichte einer Theke finden

        for artikel in artikel_liste:
            # Wir suchen zuerst im Artikel, falls nicht da, schauen wir im Theken-Container
            datum = artikel.get('data-date') or theke.get('data-date') or "Unbekannt"
            standort = artikel.get('data-standort') or theke.get('data-standort') or "Unbekannt"
            theke_attr = artikel.get('data-theke') or theke.get('data-theke') or "Unbekannt"

            title_tag = artikel.find('div', class_='title') # Titel extrahieren
            title = title_tag.text.strip() if title_tag else "Unbekannt"

            score_tag = artikel.find('div', class_='score') # Bewertung extrahieren
            score = score_tag.text.strip() if score_tag else "0,0"

            price_stud = artikel.find('div', class_='price', attrs={'data-type': 'student'}) # Preis für Studierende extrahieren
            preis = price_stud.text.strip() if price_stud else "Unbekannt"

            img_tag = artikel.find('img', alt='Foto: Mahlzeit auf dem Teller') # Bild-URL extrahieren
            img_url = ""
            if img_tag and 'src' in img_tag.attrs:
                img_url = "https://mensa.studiwerk.de" + img_tag['src']


            meals_list.append({ # Alle Daten als dictionary in Liste schreiben
                "Datum": datum,
                "Standort": standort,
                "Theke": theke_attr,
                "Kategorie": kategorie,
                "Gericht": title,
                "Bewertung": score,
                "Preis (Studierende)": preis,
                "Bild": img_url
            })
    return meals_list


def mensa_get_df_raw(meals_list):
    """
    Kombiniert die gesammelten Daten in ein Pandas DataFrame.
    """
    df = pd.DataFrame(meals_list)
    return df

def mensa_get_df(df):
    """
    Nimmt das rohe DataFrame, formatiert das Datum und übersetzt die Standort-IDs.
    """
    df["Datum"] = pd.to_datetime(df["Datum"], format="%Y%m%d", errors="coerce") # Wandelt den String (z.B. '20260424') zuerst in ein Pandas-Datum um
    df["Datum"] = df["Datum"].dt.strftime("%Y-%m-%d") # Formatiert das Datum in ein lesbareres Format

    standort_mapping = { # Ordnet den Standorten die tatsächlichen Namen zu
        "standort-1": "Tarforst",
        "standort-7": "Oliva",
        "standort-3": "Petrisberg",
        "standort-4": "Schneidershof",
        "standort-9": "Bellevue",
        "standort-5": "Irminenfreihof"
    }

    df["Standort"] = df["Standort"].replace(standort_mapping) # Ersetzt die Namen der Standorte

    return df
