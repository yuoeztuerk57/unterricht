from datetime import datetime, timedelta

MWST_SATZ = 0.19
PREMIUM_RABATT = 0.10
FREIVERSAND_AB = 100.0  # Warenkorbwert, ab dem die Standard-Versandkosten entfallen

# Teil 2: Tupel für unveränderliche Versandtarife
VERSANDTARIFE = (("Standard", 4.90), ("Express", 12.50))

# Bekannte Rabattcodes (bereinigt, Großbuchstaben) -> Rabattsatz
RABATTCODES = {"SOMMER2026": 0.05}


# Teil 1: Datenmodell

class Produkt:

    def __init__(self, produkt_id: str, name: str, preis: float,
                lagerbestand: int, kategorie: str = "Sonstiges") -> None:
        self.produkt_id = produkt_id
        self.name = name
        self.preis = preis
        self.lagerbestand = lagerbestand
        self.kategorie = kategorie

    def __str__(self) -> str:
        return (f"{self.produkt_id}: {self.name} - {self.preis:.2f} € "
                f"(Bestand: {self.lagerbestand})")


class Kunde:

    def __init__(self, kunden_id: str, name: str, ist_premium: bool = False) -> None:
        self.kunden_id = kunden_id
        self.name = name
        self.ist_premium = ist_premium


class LagerbestandNichtAusreichendError(Exception):
    """Wird ausgelöst, wenn mehr Artikel bestellt werden, als auf Lager sind."""



# Teil 2: Sortiment (Dictionary) und Kategorien (Set)

def erstelle_sortiment(produkte: list[Produkt]) -> tuple[dict[str, Produkt], set[str]]:
    sortiment = {p.produkt_id: p for p in produkte}
    kategorien = {p.kategorie for p in produkte}
    return sortiment, kategorien



# Teil 3: Preiskalkulation

def berechne_gesamtsumme(warenkorb: list[Produkt], kunde: Kunde,
                        rabattcode: str = "", versandart: str = "Standard") -> float:
    summe = sum(p.preis for p in warenkorb)

    if kunde.ist_premium:
        summe *= 1 - PREMIUM_RABATT

    code = rabattcode.strip().upper()
    if code in RABATTCODES:
        summe *= 1 - RABATTCODES[code]
    elif code:
        print(f"  Hinweis: Rabattcode '{code}' ist unbekannt und wird ignoriert.")

    versandkosten = dict(VERSANDTARIFE)[versandart]
    if versandart == "Standard" and summe > FREIVERSAND_AB:
        versandkosten = 0.0

    brutto = summe * (1 + MWST_SATZ)
    return round(brutto + versandkosten, 2)



# Teil 4: Datum und Zeit

def berechne_lieferdatum(start: datetime, werktage: int = 3) -> datetime:

    datum = start
    verbleibend = werktage
    while verbleibend > 0:
        datum += timedelta(days=1)
        if datum.weekday() < 5:
            verbleibend -= 1
    return datum


def formatiere_datum(datum: datetime) -> str:

    return datum.strftime("%d.%m.%Y %H:%M Uhr")


class Bestellung:

    def __init__(self, kunde: Kunde, warenkorb: list[Produkt], gesamtsumme: float) -> None:
        self.kunde = kunde
        self.warenkorb = warenkorb
        self.gesamtsumme = gesamtsumme
        self.erstellt_am = datetime.now()
        self.lieferdatum = berechne_lieferdatum(self.erstellt_am)

    def __str__(self) -> str:
        return (f"Bestellung von {self.kunde.name}: {len(self.warenkorb)} Artikel, "
                f"{self.gesamtsumme:.2f} €\n"
                f"  Bestellt am:        {formatiere_datum(self.erstellt_am)}\n"
                f"  Voraussichtliche Lieferung: {formatiere_datum(self.lieferdatum)}")


# Teil 5: Robuste Artikelbestellung
def bestelle_artikel(sortiment: dict[str, Produkt], produkt_id: str,
                    menge_eingabe: str) -> int:

    print(f"\n> Bestellung: {produkt_id}, Menge '{menge_eingabe}'")
    try:
        menge = int(menge_eingabe)  # ValueError bei "abc"
        if menge <= 0:
            raise ValueError("Menge muss größer als 0 sein.")
        produkt = sortiment[produkt_id]  # KeyError bei unbekannter ID
        if menge > produkt.lagerbestand:
            raise LagerbestandNichtAusreichendError(
                f"{produkt.name}: {menge} bestellt, nur {produkt.lagerbestand} auf Lager."
            )
    except ValueError as err:
        print(f"  [FEHLER] Ungültige Menge '{menge_eingabe}': {err}")
        return 0
    except KeyError:
        print(f"  [FEHLER] Unbekannte Produkt-ID '{produkt_id}'.")
        return 0
    except LagerbestandNichtAusreichendError as err:
        print(f"  [FEHLER] Lagerbestand nicht ausreichend – {err}")
        return 0
    else:
        produkt.lagerbestand -= menge
        print(f"  [OK] {menge} x {produkt.name} gebucht. Neuer Bestand: {produkt.lagerbestand}")
        return menge
    finally:
        print("  [SYSTEM] Transaktion abgeschlossen.")


# Hauptprogramm
if __name__ == "__main__":
    sortiment, kategorien = erstelle_sortiment([
        Produkt("PROD-101", "Laptop", 899.99, 15, "Elektronik"),
        Produkt("PROD-102", "Maus", 25.00, 50, "Elektronik"),
        Produkt("PROD-103", "Schreibtisch", 249.90, 3, "Büro"),
        Produkt("PROD-104", "Notizblock", 4.50, 200, "Büro"),
    ])

    print("Sortiment")
    for produkt in sortiment.values():
        print(produkt)
    print("Kategorien:", ", ".join(sorted(kategorien)))
    print("Versandtarife:", "; ".join(f"{n} {p:.2f} €" for n, p in VERSANDTARIFE))

    print("\nArtikelbestellung mit Fehlerbehandlung")
    bestelle_artikel(sortiment, "PROD-101", "2")    # erfolgreich
    bestelle_artikel(sortiment, "PROD-102", "abc")  # ValueError
    bestelle_artikel(sortiment, "PROD-103", "10")   # zu wenig Lagerbestand
    bestelle_artikel(sortiment, "PROD-999", "1")    # unbekannte ID

    print("\nPreiskalkulation")
    premium = Kunde("K-1", "Anna Beispiel", ist_premium=True)
    standard = Kunde("K-2", "Ben Muster")
    warenkorb = [sortiment["PROD-101"]] * 2 + [sortiment["PROD-102"]]
    kleiner_warenkorb = [sortiment["PROD-104"]] * 2

    summe_premium = berechne_gesamtsumme(warenkorb, premium, "  sommer2026 ")
    summe_standard = berechne_gesamtsumme(warenkorb, standard)
    summe_klein = berechne_gesamtsumme(kleiner_warenkorb, standard)
    print(f"Premium-Kunde mit Code:        {summe_premium:.2f} €")
    print(f"Standard-Kunde ohne Code:      {summe_standard:.2f} €")
    print(f"Kleiner Warenkorb (mit Porto): {summe_klein:.2f} €")

    print("\nBestellung & Lieferdatum")
    print(Bestellung(premium, warenkorb, summe_premium))