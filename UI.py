from Scraping import mensa_get_html, mensa_get_data, mensa_get_df, mensa_get_df_raw
from supabase import create_client, Client
import streamlit as st
import plotly.express as px
import pandas as pd

@st.cache_data(ttl=3600) # Speichert die tagesaktuellen Daten im Cache, sodass die Mensawebsite nur maximal stündlich gescrapt wird
def load_data(url):
    html = mensa_get_html(url)
    rohdaten = mensa_get_data(html)
    df_raw = mensa_get_df_raw(rohdaten)
    df = mensa_get_df(df_raw)
    return df

# Link zur Mensa-Website
mensa_url = "https://mensa.studiwerk.de/standort/schneidershof"

# Supabase Verbindung mit geheimer URL und Key
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

# Seitenkonfiguration
st.set_page_config(page_title="Mensa Speiseplan", page_icon="🍔", layout="wide")
st.title("🍔 Mensa-App")

try:
    # Supabase Client zur Verbindung zur Datenbank
    supabase: Client = create_client(supabase_url, supabase_key)
    st.toast("Mit Datenbank verbunden", icon="✅")

except Exception as e:
    st.error(f"Konnte nicht mit Supabase verbinden: {e}")


with st.spinner("Lade aktuellen Speiseplan herunter..."):
    df_mensa_heute = load_data(mensa_url)

dict_mensa_heute = df_mensa_heute.to_dict(orient="records") # Wandelt erzeugtes Dataframe für Supabase wieder in Dictionary um

try:
    supabase.table("mensa_historie").upsert(dict_mensa_heute, on_conflict="Datum,Standort,Gericht").execute() # Aktualisiert die Daten in der Datenbank ohne Duplikate zu erzeugen
    st.toast("Heutige Daten erfolgreich in der Datenbank gespeichert!", icon = "💾")

except Exception as e:
    st.error(f"Fehler beim Speichern in Supabase: {e}") # Fehler anzeigen, wenn aktualisieren fehlgeschlagen

response = supabase.table("mensa_historie").select("*").execute() # Lädt die gesamte Datenbank herunter

df_mensa = pd.DataFrame(response.data) # Wandelt die Daten aus der Datenbank wieder in ein Dataframe um

tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top 20", "🚩 Flop 20", "🍳 Meistgekocht", "📍 Standortvergleich"]) #

with tab4:
    df_mensa["Bewertung"] = df_mensa["Bewertung"].astype(str) # Sicherstellen, dass alles als Text behandelt wird (für den replace-Befehl)
    df_mensa["Bewertung"] = df_mensa["Bewertung"].str.replace(',', '.') # Komma durch Punkt ersetzen für folgende Umwandlung
    df_mensa["Bewertung"] = pd.to_numeric(df_mensa["Bewertung"], errors="coerce") # Bewertung von Text in echte Zahl umwandeln für Berechnungen, NaN wenn keine Zahl
    df_gefiltert = df_mensa[df_mensa["Bewertung"] > 0] # 0 Sterne Bewertungen rausfiltern, da noch keine Bewertung vorhanden
    df_durchschnitt = df_gefiltert.groupby(["Datum", "Standort"])["Bewertung"].mean().reset_index() # Durchschnitt berechnen und Datum sowie Standort zuordnen

    fig = px.line( # Konfigurieren des Plots
        df_durchschnitt,
        x="Datum", # X-Achse: Tage
        y="Bewertung", # Y-Achse: Durchschnitt
        color="Standort", # Jede Mensa bekommt eine zufällige Farbe
        markers=True, # Setzt Punkte auf die einzelnen Tage
        title="📈 Durchschnittliche Sternebewertung im Zeitverlauf",
        range_y=[0, 5], # Skala fest auf 0 bis 5 Sterne setzen
        labels={"Bewertung": "Ø Bewertung (Sterne)"}
    )

    st.plotly_chart(fig, use_container_width=True) # Plot in Streamlit anzeigen

with tab1:
    st.subheader("Die Top 20 Gerichte aller Zeiten")

    top10_df = df_mensa.sort_values(by="Bewertung", ascending=False).drop_duplicates(subset=["Gericht"]).head(20) # speichert die ersten 10 Einträge des Dataframes sortiert nach Bewertung ohne Duplikate

    platz = 1

    # 2. Schleife durch die Top 10 Gerichte
    for index, row in top10_df.iterrows(): # Iteration über die Dataframe-Elemente nach Index und Verarbeitung der Daten in der Zeile "row"

        col1, col2 = st.columns([1, 3]) # Zweispaltige Ansicht im Verhältnis 1:3

        with col1:
            foto_link = row["Bild"] # lädt die passende Bild-URL
            if pd.notna(foto_link) and foto_link != "": # prüft ob überhaupt ein Bild hinterlegt ist
                st.image(foto_link, use_container_width=True) # platziert das Bild
            else:
                st.info("Kein Bild vorhanden 🍽️")

        with col2:
            st.markdown(f"### #{platz} {row['Gericht']}") # Der Name des Gerichts als Überschrift
            st.metric(label="Sternebewertung", value=f"⭐ {row['Bewertung']}") # Bewertung
            st.caption(f"📍 Zuletzt gesehen in: {row['Standort']}") # Wo es das Gericht zuletzt gab

        platz += 1

with tab2:
    st.subheader("Die Flop 20 Gerichte aller Zeiten")

    df_gefiltert = df_mensa[df_mensa["Bewertung"] > 0]  # 0 Sterne Bewertungen rausfiltern, da noch keine Bewertung vorhanden
    flop10_df = df_gefiltert.sort_values(by="Bewertung", ascending=True).drop_duplicates(subset=["Gericht"]).head(20)

    platz = 1

    # 2. Schleife durch die Flop 10 Gerichte
    for index, row in flop10_df.iterrows():

        col1, col2 = st.columns([1, 3])
        with col1:
            foto_link = row["Bild"]
            if pd.notna(foto_link) and foto_link != "":
                st.image(foto_link, use_container_width=True)
            else:
                st.info("Kein Bild vorhanden 🍽️")

        with col2:
            st.markdown(f"### #{platz} {row['Gericht']}")
            st.metric(label="Sternebewertung", value=f"⭐ {row['Bewertung']}")
            st.caption(f"📍 Zuletzt gesehen in: {row['Standort']}")

        platz += 1

with tab3:
    df_meistgekocht = df_mensa['Gericht'].value_counts().head(10).reset_index()
    df_meistgekocht.columns = ['Gericht', 'Anzahl'] # Spalten benennen
    df_meistgekocht = df_meistgekocht.sort_values('Anzahl', ascending=True) # Sortierung

    fig = px.bar(
        df_meistgekocht,
        x='Anzahl',
        y='Gericht',
        orientation='h', # Horizontal
        title='🍳 Die Top 10 der meistgekochten Gerichte',
        text_auto=True # Zeigt die genaue Anzahl direkt am Balken an
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

with st.expander("Dataframe"): # Zeigt das Dataframe im ausklappbaren Menü an
    st.dataframe(df_mensa, use_container_width=True)

html_snippet = """
          <article id="article-341791-standort-1" class="theke-slider-item" data-standort="standort-1" data-theke="theke-1" data-date="20260424" data-meal="341791" aria-label="Mahlzeit (für Details anklicken...)" data-vegan="yes" data-laktose="yes" data-alkohol="yes" data-veggie="yes" data-gluten="no">
            <div class="card">
              <div class="score" aria-label="Durchschnittliche Bewertung Anzahl Sterne von 5 Sternen:">4,4</div>
              <div class="meal">
                <div class="main-meal">
                  <div class="image">
                    <img src="/eo/media?s=mensa-startseite&amp;id=100155" alt="Foto: Mahlzeit auf dem Teller" data-komponente-id="341790" data-cmp-info="10">
                  </div>
                </div>
                <div class="prices">
                  <div class="price" data-type="student" aria-label="Preis Studenten">3,20 €</div>
                  <div class="price" data-type="mitarbeiter" aria-label="Preis Mitarbeiter">4,80 €</div>
                  <div class="price" data-type="gaeste" aria-label="Preis Gäste">6,60 €</div>
                  <div class="co2"><span class="meta-element">CO2 Wert in Gramm:</span>431 g<br></div>
                </div>
              </div>
              <div class="title">Linsen-Curry mit Kokosmilch gebratenem Tofu und Vollkornreis</div>
            </div>
          </article>"""


with st.expander("HTML-Snippet (Beispiel)"): # Zeigt ein beispielhaftes HTML-Snippet im ausklappbaren Menü an
    st.code(html_snippet, language="html", line_numbers=True)