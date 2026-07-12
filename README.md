# TV Missing Checker

Graphical desktop app for checking missing episodes in a local TV series
collection.

The app is bilingual. English is the default language, and Croatian can be
selected from the language menu in the app.

## What It Does

- scans a selected folder and its subfolders
- detects video files and episode markers such as `S02E05` and `2x05`
- compares local episodes with TVMaze, TMDb, TheTVDB, or IMDb data
- shows series with missing episodes
- can count only already aired episodes
- shows unrecognized files and shows that could not be matched online
- saves reports in TXT or JSON format

## Running

On Linux, from a terminal:

```bash
cd "$HOME/Desktop/TV Missing Checker"
./pokreni.sh
```

The app can also be started directly:

```bash
python3 app.py
```

On Linux, `pokreni.sh` can also be launched with a double-click if your file
manager allows executable scripts.

On Windows, run:

```text
pokreni.bat
```

## Requirements

- Python 3
- Tkinter for the graphical interface
- internet connection for online episode data

On Debian/Ubuntu-based distributions, install Tkinter if it is missing:

```bash
sudo apt install python3-tk
```

The app only uses Python's standard library; no `pip install` is required.

## API Keys

API keys are not stored in this repository.

The app stores local settings in:

```text
~/.tv_missing_checker.json
```

That file can contain the last selected folder, TMDb credentials, TheTVDB API
key, and a local TheTVDB token. Do not publish it.

TheTVDB can also be supplied through an environment variable:

```bash
export TV_MISSING_CHECKER_TVDB_API_KEY="your-key"
```

`TVDB_API_KEY` is also supported.

## Testing

Run the local parsing and matching logic tests:

```bash
python3 -m unittest -v test_app_logic.py
```

## Usage

1. Start the app.
2. Click `Browse` and select the main TV series folder.
3. Optional: enter a TMDb API key/token or TheTVDB API key.
4. Click `Start scan`.
5. Review `Missing`, `Unmatched`, and `OK` results.
6. Save a TXT or JSON report if needed.

For best results, filenames should include season and episode markers:

```text
Show.Name.S01E03.mkv
Show Name - 1x04.mp4
Show.Name.S02E05-E06.mkv
```

## Files

- `app.py` - main application
- `pokreni.sh` - Linux launcher script
- `pokreni.bat` - Windows launcher script
- `test_app_logic.py` - local logic tests
- `README.md` - project instructions

---

# TV Missing Checker

Graficki desktop program za provjeru nedostajucih epizoda u lokalnoj kolekciji
TV serija.

Program je dvojezican. Engleski je zadani jezik, a hrvatski se moze odabrati u
izborniku jezika unutar aplikacije.

## Sto Program Radi

- skenira odabrani folder i njegove podfoldere
- prepoznaje video datoteke i oznake epizoda poput `S02E05` i `2x05`
- usporeduje lokalne epizode s podacima na TVMazeu, TMDb-u, TheTVDB-u ili IMDb-u
- prikazuje serije kojima nedostaju epizode
- moze racunati samo vec emitirane epizode
- prikazuje neprepoznate datoteke i serije koje nije uspio pronaci
- sprema izvjestaj u TXT ili JSON formatu

## Pokretanje

Na Linuxu, u terminalu:

```bash
cd "$HOME/Desktop/TV Missing Checker"
./pokreni.sh
```

Program se moze pokrenuti i izravno:

```bash
python3 app.py
```

Na Linuxu je moguce dvaput kliknuti na `pokreni.sh` ako upravitelj datoteka
dopusta izvrsavanje skripti.

Na Windowsu pokreni:

```text
pokreni.bat
```

## Preduvjeti

- Python 3
- Tkinter za graficko sucelje
- internetska veza za dohvat popisa epizoda

Na distribucijama temeljenima na Debianu ili Ubuntuu Tkinter se, ako nedostaje,
instalira naredbom:

```bash
sudo apt install python3-tk
```

Program koristi samo Pythonovu standardnu biblioteku; nije potreban
`pip install`.

## API Kljucevi

API kljucevi se ne spremaju u ovaj repozitorij.

Program lokalne postavke sprema u:

```text
~/.tv_missing_checker.json
```

Ta datoteka moze sadrzavati zadnji odabrani folder, TMDb podatke, TheTVDB API
kljuc i lokalni TheTVDB token. Nemoj je javno dijeliti.

TheTVDB kljuc moze se zadati i kroz environment varijablu:

```bash
export TV_MISSING_CHECKER_TVDB_API_KEY="tvoj-kljuc"
```

Podrzan je i `TVDB_API_KEY`.

## Testiranje

Pokreni lokalne testove parsiranja i matchanja:

```bash
python3 -m unittest -v test_app_logic.py
```

## Koristenje

1. Pokreni program.
2. Klikni `Browse` i odaberi glavni folder sa serijama.
3. Po zelji unesi TMDb API kljuc/token ili TheTVDB API kljuc.
4. Klikni `Start scan`.
5. Pregledaj rezultate `Missing`, `Unmatched` i `OK`.
6. Po potrebi spremi TXT ili JSON izvjestaj.

Za najbolje rezultate nazivi datoteka trebaju sadrzavati sezonu i epizodu:

```text
Naziv.Serije.S01E03.mkv
Naziv Serije - 1x04.mp4
Naziv.Serije.S02E05-E06.mkv
```

## Datoteke

- `app.py` - glavni program
- `pokreni.sh` - Linux skripta za pokretanje
- `pokreni.bat` - Windows skripta za pokretanje
- `test_app_logic.py` - lokalni testovi logike
- `README.md` - upute
