# Brev til borgere omkring frivillig indbetaling

Robotten sender digitale breve til borgere med frivillige afdragsordninger (lån) for at informere dem om muligheden for at undgå renter.

## Hvad gør robotten?

1. Indlæser en Excel-fil med borgere (CPR-nummer, navn, adresse, restgæld, lånebeløb) og opretter arbejdskøposter (`--queue` flag). Excel-filen slettes automatisk efter indlæsning.
2. Validerer borgerens adresse mod Datafordeler. Borgere med ikke-matchende adresser sendes til manuel behandling med angivet årsag.
3. Søger efter en eksisterende SBSYS-sag af typen "Frivillig afdrag - Ydelse" (skabelon ID 2942). Genåbner en lukket sag frem for at oprette en ny.
4. Genererer et PDF-brev ved at flette borgerdata ind i en Word-skabelon (`Brev.docx`) via en ekstern render-service.
5. Sender brevet som digital post til borgeren via SBSip.
6. Registrerer gennemførte opgaver via odk-tools Tracker og sletter midlertidige PDF-filer.

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø og credentials)
- Adgang til **SBSYS** (produktionsmiljø)
- Adgang til **SBSip** (produktionsmiljø)
- Certifikater til **Datafordeler** (adressevalidering)

## Installation

```sh
uv sync
```

## Konfiguration

Credentials registreres i Automation Server:
- `SBSYS - produktion`
- `SBSip - produktion`
- `Odense SQL Server`

| Miljøvariabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server API |
| `ATS_TOKEN` | Bearer token til Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | Tilsidesæt arbejdskø-ID (valgfri) |
| `CERTIFIKATER` | Sti til mappe med Datafordeler-certifikater (standard: `/certifikater`) |

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen fra Excel-fil
uv run python main.py           # Behandl arbejdskøen
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Workqueue-håndtering og credentials fra Automation Server |
| `datafordeler` | Adressevalidering af borgere via Datafordeler-API med certifikat |
| `odk-tools` | Opgavesporing (Tracker) og fejlrapportering |
| `openpyxl` | Læsning af Excel-filer med borgerdata |
| `sbsip` | Afsendelse af digital post til borgere |
| `sbsys` | SBSYS-sagsstyring: søgning, genåbning og oprettelse af sager |

## GDPR og sikkerhed

Processen behandler følsomme personoplysninger: CPR-numre, navne, adresser, restgæld og lånebeløb for borgere med frivillige afdragsordninger. Oplysningerne hentes fra en Excel-fil, der slettes automatisk efter indlæsning i arbejdskøen. Data behandles kun i hukommelsen under kørsel og sendes til borgeren som digital post via SBSip. Fejlrapporter med borgerdata er tilgængelige via Automation Server.
