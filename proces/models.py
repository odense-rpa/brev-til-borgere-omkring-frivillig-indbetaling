from pydantic import BaseModel, field_validator
from typing import Optional
import re

def valider_cpr(v: str) -> str:
    v = v.strip()
    if re.fullmatch(r"\d{10}", v):
        v = v[:6] + "-" + v[6:]
    if not re.fullmatch(r"\d{6}-\d{4}", v):
        raise ValueError("CPR skal have formatet DDMMÅÅ-XXXX")
    return v



class PersonAdresse(BaseModel):
    Vejnavn:str
    Husnummer:str
    Etage:Optional[str] = None
    Dør:Optional[str] = None
    Postnummer:int
    By:str
    AdresseTekst:str

    @classmethod
    def from_string(cls, adresse: str) -> "PersonAdresse":
        # Extract postnummer and by from last segment after last ", "
        last_comma = adresse.rfind(", ")
        postnummer_by = adresse[last_comma + 2:]
        rest = adresse[:last_comma]

        postnummer_match = re.match(r"(\d+)\s+(.+)", postnummer_by)
        if not postnummer_match:
            raise ValueError(f"Kan ikke parse postnummer/by fra: {postnummer_by}")
        postnummer = int(postnummer_match.group(1))
        by = postnummer_match.group(2)

        # Split on first comma to separate vejnavn+husnummer from etage/dør
        first_comma = rest.find(",")
        if first_comma == -1:
            vejnavn_husnummer = rest.strip()
            etage_dør_str = ""
        else:
            vejnavn_husnummer = rest[:first_comma].strip()
            etage_dør_str = rest[first_comma + 1:].split(",")[0].strip()

        # Parse vejnavn and husnummer: husnummer is last token starting with a digit
        vh_match = re.match(r"^(.*?)\s+(\d+\w*)$", vejnavn_husnummer)
        if not vh_match:
            raise ValueError(f"Kan ikke parse vejnavn/husnummer fra: {vejnavn_husnummer}")
        vejnavn = vh_match.group(1)
        husnummer = vh_match.group(2)

        # Parse etage and dør from "etage.dør" pattern (e.g. "01.tv", "st.4", "02.")
        etage = None
        dør = None
        if etage_dør_str:
            if "." in etage_dør_str:
                dot_idx = etage_dør_str.index(".")
                etage = etage_dør_str[:dot_idx] or None
                dør = etage_dør_str[dot_idx + 1:] or None
            else:
                etage = etage_dør_str or None

        return cls(
            Vejnavn=vejnavn,
            Husnummer=husnummer,
            Etage=etage,
            Dør=dør,
            Postnummer=postnummer,
            By=by,
            AdresseTekst=adresse,
        )

class Person(BaseModel):
    Cpr:str
    Navn:str
    Adresse:PersonAdresse
    Restgæld:str
    Lånebeløb:str
    
    @field_validator("Cpr")
    @classmethod
    def valider_cpr(cls, v: str) -> str:
        return valider_cpr(v)