from sbsys.manager import SbsysClientManager
from proces.models import Person
import logging
import sbsip
from datafordeler.datafordeler import Datafordeler
from proces.datafordeler_service import DatafordelerService
from datetime import date
import json
from pathlib import Path
import httpx

class SbsysService:
    def __init__(
        self,
        sbsys: SbsysClientManager
        ):
        self.sbsys = sbsys
    
    async def find_og_åben_sag(self, borger:Person):
        logger = logging.getLogger(__name__)
        
        logger.info("Henter sag af sagstype 'Frivillig afdrag -Ydelse'")
        query = {
            "PrimaerPerson":{
                    "CprNummer":borger.Cpr
                },
                "SagsSkabeloner":[
                    2942
                ]
        }
        sager = await self.sbsys.sager.søg_sager(query)

        igangværende = [sag for sag in sager if sag["SagsStatus"]["SagsTilstand"] == "Igangværende"]
        kandidater = igangværende if igangværende else sager

        sag = max(kandidater, key=lambda s: s.get("Oprettet", "")) if kandidater else None
                    
        logger.info("Kontrollere om borger allerede har åben sag af sagstype")
        if sag is not None and sag["SagsStatus"]["SagsTilstand"] == "Aktiv":
            logger.info("Åben sag af sagstype findes allerede")
        elif sag is not None:
            logger.info("Ingen åben sag fundet, genåbner den nyeste lukket af sagstype")
            await self.sbsys.sager.opdater_sagsstatus(sag["Id"], "Igangværende", "Opdateret af Tyra")
        else:
            logger.info("Ingen sag af sagstype fundet, der skal oprettes en ny")
    
    @staticmethod
    def send_brev_og_opret_sag(borger: Person, fil_sti: str, fordeler: Datafordeler):
        logger = logging.getLogger(__name__)
        
        brev_felter = {
            "NAVN": borger.Navn,
            "CPR": borger.Cpr,
            "ADRESSE": borger.Adresse.AdresseTekst,
            "DAGSDATO": date.today().strftime("%d-%m-%Y"),
            "RESTGÆLD": borger.Restgæld,
            "LÅNEBELØB": borger.Lånebeløb
        }
        
        logger.info("Prøver at flette brevet")
        try:
            with open(
                fil_sti, "rb"
            ) as f:
                response = httpx.post(
                    "http://rpa-ats.odknet.dk:8331/render",
                    files={
                        "file": (fil_sti, f)
                    },
                    data={"fields": json.dumps(brev_felter)}     
                )
        except Exception as e:
            logger.error(e)
            raise RuntimeError("Teknisk fejl: Kunne ikke danne brev")
            
        pdf_path = Path("frivillig_brev.pdf")
        pdf_path.write_bytes(response.content)
        
        cpr_uden_bindestreg = borger.Cpr.replace("-","")
        
        adresse, post_nr = fordeler.hent_adresse_til_sbsip(cpr_uden_bindestreg)

        try:
            sbsip.send_digital_post(
                cpr=cpr_uden_bindestreg,
                overskrift="Frivilligt afdrag - vil du undgå renter",
                beskrivelse="Frivilligt afdrag - vil du undgå renter",
                vedhæftet_fil=pdf_path,
                post_nr=post_nr,
                adresse=adresse,
                sbsys_skabelon_id="2942"
            )
        except Exception as e:
            logger.error(e)
            pdf_path.unlink()
            raise RuntimeError("Teknisk fejl: Kunne ikke sende brev")
        
        pdf_path.unlink()