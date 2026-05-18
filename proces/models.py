from pydantic import BaseModel, field_validator
import re

def valider_cpr(v: str) -> str:
    v = v.strip()
    if re.fullmatch(r"\d{10}", v):
        v = v[:6] + "-" + v[6:]
    if not re.fullmatch(r"\d{6}-\d{4}", v):
        raise ValueError("CPR skal have formatet DDMMÅÅ-XXXX")
    return v


class Person(BaseModel):
    Cpr:str
    Navn:str
    Adresse:str
    Restgæld:str
    Lånebeløb:str
    
    @field_validator("Cpr")
    @classmethod
    def valider_cpr(cls, v: str) -> str:
        return valider_cpr(v)