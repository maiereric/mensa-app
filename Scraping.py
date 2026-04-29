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

    # Finde alle "Theken" (Kategorien wie Pflanzenfein, Da Capo etc.)
    theken = soup.find_all('div', attrs={'data-type': 'theke-slider'})

    for theke in theken:
        # 1. Kategorie-Namen herausfinden (Label im HTML)
        kategorie_tag = theke.find('span', class_='label')
        kategorie = kategorie_tag.text.strip() if kategorie_tag else "Unbekannt"

        # 2. Alle Gerichte innerhalb dieser Kategorie finden
        artikel_liste = theke.find_all('article', class_='theke-slider-item')

        for artikel in artikel_liste:

            # Wir suchen zuerst im Artikel, falls nicht da, schauen wir im Theken-Container
            datum = artikel.get('data-date') or theke.get('data-date') or "Unbekannt"
            standort = artikel.get('data-standort') or theke.get('data-standort') or "Unbekannt"
            theke_attr = artikel.get('data-theke') or theke.get('data-theke') or "Unbekannt"

            # Titel extrahieren
            title_tag = artikel.find('div', class_='title')
            title = title_tag.text.strip() if title_tag else "Kein Titel"

            # Bewertung extrahieren
            score_tag = artikel.find('div', class_='score')
            score = score_tag.text.strip() if score_tag else "0,0"

            # Preis für Studierende extrahieren
            price_stud = artikel.find('div', class_='price', attrs={'data-type': 'student'})
            preis = price_stud.text.strip() if price_stud else "N/A"

            # Bild-URL extrahieren
            img_tag = artikel.find('img', alt='Foto: Mahlzeit auf dem Teller')
            img_url = ""
            if img_tag and 'src' in img_tag.attrs:
                img_url = "https://mensa.studiwerk.de" + img_tag['src']

            # Alles als Paket in unsere Liste packen
            meals_list.append({
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
    print("Verfügbare Spalten:", df.columns)
    print("Anzahl Zeilen:", len(df))
    """
    Nimmt das rohe DataFrame, formatiert das Datum und übersetzt die Standort-IDs.
    """
    # --- 1. Datum formatieren ---
    # Wandelt den String (z.B. '20260424') zuerst in ein echtes Pandas-Datum um
    df["Datum"] = pd.to_datetime(df["Datum"], format="%Y%m%d", errors="coerce")
    df["Datum"] = df["Datum"].dt.strftime("%Y-%m-%d")
    # Formatiert das Datum in ein schönes deutsches Format (z.B. 24.04.2026)

    # --- 2. Standorte umbenennen ---
    standort_mapping = {
        "standort-1": "Tarforst",
        "standort-7": "Oliva",
        "standort-3": "Petrisberg",
        "standort-4": "Schneidershof",
        "standort-9": "Bellevue",
        "standort-5": "Irminenfreihof"
    }

    # Die replace-Funktion sucht in der Spalte nach den Schlüsseln (links)
    # und ersetzt sie durch die Werte (rechts).
    df["Standort"] = df["Standort"].replace(standort_mapping)

    return df
