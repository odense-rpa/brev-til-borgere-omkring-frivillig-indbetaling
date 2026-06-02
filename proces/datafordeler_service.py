from datafordeler.datafordeler import Datafordeler
from proces.models import Person

class DatafordelerService:
    @staticmethod
    def korrekt_adresse(borger: Person, datafordeler: Datafordeler) -> bool:
        cpr_uden_bindestreg = borger.Cpr.replace("-","")
        borger_adresse = datafordeler.hent_aktiv_adresse(cpr_uden_bindestreg)
        
        if borger_adresse is None:
            return False

        cpr_adresse = borger_adresse["Adresseoplysninger"]["CprAdresse"]

        cpr_adresse["husnummer"] = cpr_adresse["husnummer"].lstrip("0")
        
        if borger.Adresse.Vejnavn == cpr_adresse["vejadresseringsnavn"] and borger.Adresse.Husnummer == cpr_adresse["husnummer"] and borger.Adresse.Postnummer == int(cpr_adresse["postnummer"]) and borger.Adresse.By == cpr_adresse["postdistrikt"]:
            if "etage" in cpr_adresse:
                if borger.Adresse.Etage is None or borger.Adresse.Etage.lstrip("0") != cpr_adresse["etage"].lstrip("0"):
                    return False
            if "sidedoer" in cpr_adresse:
                if borger.Adresse.Dør is None or borger.Adresse.Dør.lstrip("0") != cpr_adresse["sidedoer"].lstrip("0"):
                    return False            
            return True
        else:
            return False