from datafordeler.datafordeler import Datafordeler
from automation_server_client import WorkItemError
from proces.models import Person

class DatafordelerService:
    @staticmethod
    def korrekt_adresse(borger: Person, datafordeler: Datafordeler) -> bool:
        cpr_uden_bindestreg = borger.Cpr.replace("-","")
        
        try:
            borger_adresse = datafordeler.hent_aktiv_adresse(cpr_uden_bindestreg)
        except ValueError as e:
            raise WorkItemError(f"Teknisk fejl: {e}")
        except Exception as e:
            raise WorkItemError(f"Teknisk fejl: Kunne ikke hente adresse fra datafordeler for borger")
        
        if borger_adresse is None:
            return False

        cpr_adresse = borger_adresse["Adresseoplysninger"]["CprAdresse"]
        
        if cpr_adresse["postdistrikt"] == "Ukendt":
            return False

        cpr_adresse["husnummer"] = cpr_adresse["husnummer"].lstrip("0")
        
        if borger.Adresse.Vejnavn.casefold() == cpr_adresse["vejadresseringsnavn"].casefold() and borger.Adresse.Husnummer.casefold() == cpr_adresse["husnummer"].casefold() and borger.Adresse.Postnummer == int(cpr_adresse["postnummer"]) and borger.Adresse.By.casefold() == cpr_adresse["postdistrikt"].casefold():
            if "etage" in cpr_adresse:
                if borger.Adresse.Etage is None or borger.Adresse.Etage.lstrip("0").casefold() != cpr_adresse["etage"].lstrip("0").casefold():
                    return False
            if "sidedoer" in cpr_adresse:
                if borger.Adresse.Dør is None or borger.Adresse.Dør.lstrip("0").casefold() != cpr_adresse["sidedoer"].lstrip("0").casefold():
                    return False            
            return True
        else:
            return False