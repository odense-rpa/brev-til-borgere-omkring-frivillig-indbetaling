import asyncio
import argparse
import csv
import logging
import os

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential, WorkItemStatus
from sbsys.manager import SbsysClientManager
from odk_tools.tracking import Tracker
from datafordeler import DatafordelerGraphQL
import sbsip
from pathlib import Path
from odk_tools.reporting import report

from proces.models import Person, PersonAdresse
from proces.datafordeler_service import DatafordelerService
from proces.sbsys_service import SbsysService

sbsys: SbsysClientManager
tracker: Tracker
datafordeler: DatafordelerGraphQL
sbsys_service: SbsysService


procesnavn = "Brev til borgere vedrørende frivillig indbetaling"

async def populate_queue(workqueue: Workqueue, csv_sti: str):
    logger = logging.getLogger(__name__)

    logger.info("Indlæser csv fil")
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(csv_sti, newline="", encoding=encoding) as csv_fil:
                sample = csv_fil.read(2048)
                csv_fil.seek(0)
                try:
                    delimiter = csv.Sniffer().sniff(sample, delimiters=";,").delimiter
                except csv.Error:
                    delimiter = ";"

                logger.info("Begynder at tilføje borgere til kø")
                for row_data in csv.DictReader(csv_fil, delimiter=delimiter):
                    borger = Person(
                        Cpr=str(row_data["Personnummer"]).zfill(10),
                        Navn=str(row_data["Navn"]),
                        Adresse=PersonAdresse.from_string(str(row_data["Adresse"])),
                        Restgæld=str(row_data["Restgæld"]),
                        Lånebeløb=str(row_data["Lånebeløb"]),
                    )

                    if not workqueue.get_item_by_reference(borger.Cpr, status=WorkItemStatus.COMPLETED):
                        workqueue.add_item(borger.model_dump(), reference=borger.Cpr)
                        logger.info(f"Added {borger.Navn} ({borger.Cpr}) to workqueue")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Kunne ikke læse csv-fil med kendte encodings: {csv_sti}")

    os.remove(csv_sti)
    logger.info(f"Slettede csv fil: {csv_sti}")

async def process_workqueue(workqueue: Workqueue, fil_sti: str):
    logger = logging.getLogger(__name__)

    logger.info("Starter med at arbejde med på køen")

    async with sbsys:
        for item in workqueue:
            with item:
                borger: Person = Person.model_validate(item.data)  # Item data deserialized from json as dict
                try:
                    if DatafordelerService.korrekt_adresse(borger, datafordeler) is not True:
                        logger.info("Adresse stemmer ikke overens med datafordeler, sendes til manuel")
                        report(
                            "brev_til_borgere_omkring_frivillig_indbetaling",
                            "Manuel",
                            json={
                                    "Cpr": borger.Cpr,
                                    "Manuel årsag": "Adresse stemmer ikke overens med datafordeler"
                            }
                        )
                        tracker.track_partial_task(procesnavn)
                        continue

                    await sbsys_service.find_og_åben_sag(borger)
                    
                    sbsys_service.send_brev_og_opret_sag(borger, fil_sti, datafordeler)
                    
                    tracker.track_task(procesnavn)                    
                        
                except WorkItemError as e:
                    # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                    logger.error(f"Error processing item: {borger}. Error: {e}")
                    report(
                            "brev_til_borgere_omkring_frivillig_indbetaling",
                            "Manuel",
                            json={
                                    "Cpr": borger.Cpr,
                                    "Manuel årsag": f"Teknisk fejl: {e}"
                            }
                        )
                    item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()
    parser = argparse.ArgumentParser(description="Brev til borgere omkring frivillig indbetaling")
    
    parser.add_argument(
        "--folder-path", 
        default=".", 
        help="Path to folder where Excel files are found"
    )
    
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Populate the workqueue from the Excel file"
    )
    parser.add_argument(
        "--word-template",
        default="Brev.docx",
        help="Path to the Word template for letter generation (default: ./Brev.docx)"
    )
    
    args = parser.parse_args()

    # Initialize external systems for automation here..
    sbsys_credential = Credential.get_credential("SBSYS - produktion")
    tracking_credential = Credential.get_credential("Odense SQL Server")
    sbsip_credential = Credential.get_credential("SBSip - produktion")
    datafordeler_credential = Credential.get_credential("Datafordeler")
    
    datafordeler = DatafordelerGraphQL(
        client_id=datafordeler_credential.username,
        client_secret=datafordeler_credential.password,
    )
    
    sbsys = SbsysClientManager(
        sbsys_credential.data["base_url"],
        sbsys_credential.data["token_url"],
        sbsys_credential.data["client_id"],
        sbsys_credential.data["client_secret"],
        sbsys_credential.username or "",
        sbsys_credential.password or ""
    )
    
    tracker = Tracker(
        username=tracking_credential.username or "",
        password=tracking_credential.password or ""
    )
    
    sbsip.start_sbsip(
        brugernavn=sbsip_credential.username or "",
        adgangskode=sbsip_credential.password or "",
    )
    
    # Queue management
    if args.queue:       
        csv_filer = list(Path(args.folder_path).glob("*.csv*"))
        if not csv_filer:
            raise FileNotFoundError(f"Ingen csv-filer fundet i: {args.folder_path}")
        csv_fil = max(csv_filer, key=lambda f: f.stat().st_mtime)
        
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue, str(csv_fil)))
        exit(0)   

    # Process workqueue
    if not Path(args.word_template).is_file():
        raise FileNotFoundError(f"Word-skabelon ikke fundet: {args.word_template}")
    sbsys_service = SbsysService(sbsys)
    asyncio.run(process_workqueue(workqueue, args.word_template))
