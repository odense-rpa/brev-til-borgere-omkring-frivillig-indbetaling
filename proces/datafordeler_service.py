from datafordeler.datafordeler import Datafordeler
from proces.models import Person

class DatafordelerService:
    @staticmethod
    def korrekt_adresse(borger: Person, datafordeler: Datafordeler) -> bool:
        borger_adresse = datafordeler.hent_aktiv_adresse(borger.Cpr)
        
        if borger_adresse is None:
            return False

        cpr_adresse = borger_adresse["Adresseoplysninger"]["CprAdresse"]

        husnummer = cpr_adresse["husnummer"].lstrip("0")
        forventet = f"{cpr_adresse['vejadresseringsnavn']} {husnummer}, {cpr_adresse['bynavn']}, {cpr_adresse['postnummer']}  {cpr_adresse['postdistrikt']}"

        return borger.Adresse.strip() == forventet.strip()