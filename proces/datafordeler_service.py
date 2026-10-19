from datafordeler import DatafordelerGraphQL
from automation_server_client import WorkItemError
from proces.models import Person

class DatafordelerService:
    @staticmethod
    def korrekt_adresse(borger: Person, datafordeler: DatafordelerGraphQL) -> bool:
        cpr_uden_bindestreg = borger.Cpr.replace("-","")
        
        try:
            cpr_adresse = datafordeler.hent_person(cpr_uden_bindestreg).adresse
        except ValueError as e:
            raise WorkItemError(f"Teknisk fejl: {e}")
        except Exception as e:
            raise WorkItemError(f"Teknisk fejl: Kunne ikke hente adresse fra datafordeler for borger")

        if cpr_adresse is None:
            raise WorkItemError("Teknisk fejl: Ingen aktiv adresse fundet i datafordeler")

        if cpr_adresse.er_ukendt:
            return False

        # Husnummer og etage er uden foranstillede nuller i datafordeler 1.0.0
        if borger.Adresse.Vejnavn.casefold() == cpr_adresse.vejadresseringsnavn.casefold() and borger.Adresse.Husnummer.casefold() == (cpr_adresse.husnummer or "").casefold() and borger.Adresse.Postnummer == int(cpr_adresse.postnummer) and borger.Adresse.By.casefold() == cpr_adresse.postdistrikt.casefold():
            if cpr_adresse.etage is not None:
                if borger.Adresse.Etage is None or borger.Adresse.Etage.lstrip("0").casefold() != cpr_adresse.etage.casefold():
                    return False
            if cpr_adresse.sidedoer is not None:
                if borger.Adresse.Dør is None or borger.Adresse.Dør.lstrip("0").casefold() != cpr_adresse.sidedoer.lstrip("0").casefold():
                    return False            
            return True
        else:
            return False