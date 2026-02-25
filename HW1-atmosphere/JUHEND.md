# Maasüsteemide kaugseire – Kodutöö nr 1 (Python + Copernicus Browser API / Sentinel Hub)

# TUDENGITE JAOTUS
| Student | Year | Variable_1 | Variable_2 |
| --- | --- | --- | --- |
| Yandar Alekseev | 2022 | NO2 | CO |
| Iiris Aljes | 2022 | O3 | NO2 |
| Arina Gotsenko | 2025 | NO2 | O3 |
| Hele-Riin Hallik | 2023 | NO2 | CH4 |
| Claudia-Isabel Huuse | 2023 | CH4 | NO2 |
| Trinity Jõgisalu | 2025 | O3 | NO2 |
| Lisette Johanson | 2024 | NO2 | CH4 |
| Katarina Kaleininkas | 2020 | CO | NO2 |
| Rene Kaur | 2020 | O3 | NO2 |
| Kaia Korman | 2021 | NO2 | CH4 |
| Nikita Lagutkin | 2024 | CH4 | O3 |
| Margot Leheroo | 2021 | CH4 | O3 |
| Helena Heliise Mardi | 2021 | CH4 | O3 |
| Regina Poom | 2025 | CH4 | CO |
| Avely-Agnes Pumalainen | 2023 | O3 | CH4 |
| Elisa Rajas | 2020 | NO2 | CO |
| Kristjan Georg Ristmäe | 2025 | CH4 | NO2 |
| Liis Seenemaa | 2023 | CH4 | O3 |
| Jaan Eerik Sorga | 2020 | O3 | NO2 |
| Grete Anette Treiman | 2022 | O3 | CH4 |
| Taavi Tunis | 2022 | CH4 | O3 |
| Heily Untera | 2022 | O3 | CO |

See repo on Sentinel‑5P (TROPOMI) Level‑2 toodete (nt **NO₂**, **CH₄**, **O₃**) visualiseerimiseks.
Töövoog on tehtud tudengitele: samm‑sammult konto loomine, Python keskkond, API ligipääs ja piltide genereerimine.

---

## 0) Mida see lahendus teeb (ülevaade)

Sa annad ette:
- **Piirkonna Euroopas** (bbox / bounding box)
- **Ajavahemiku** (näiteks üks päev)
- **2 parameetrit** (bandid): nt `NO2`, `CH4` või `O3`
- Soovi korral **projektsiooni** (EPSG), pildi mõõdud ja QA filter (`minQa`)

Skript:
1. Võtab CDSE tokeni (client_id + secret).
2. Küsib Sentinel Hub **Process API** kaudu andmed sinu AOI + aja kohta.
3. Laeb tulemuse **GeoTIFF**‑ina (float32).
4. Joonistab `matplotlib`‑iga pildi + **värviskaala** (colorbar) ja salvestab `.png`.

---

## 1) Eeldused (enne alustamist)

### Vajalikud asjad
- Internetiühendus
- Python 3.10+ (soovitus: 3.11)
- Git (repo kloonimiseks)
- CDSE konto (Copernicus Data Space Ecosystem)

### Kontroll: kas Python töötab?
Terminalis / käsureal:
```bash
python --version
```
Kui käsu asemel tuleb “not found”, paigalda Python (Windowsis vali installeri juures **Add Python to PATH**).

---

## 2) CDSE konto ja API ligipääs (kõige olulisem osa)

### 2.1 Loo CDSE kasutaja
1. Ava Copernicus Data Space Ecosystem (CDSE) portaal ja registreeru.
2. Logi sisse.

### 2.2 Loo OAuth klient (client_id + client_secret)
1. Ava CDSE **Dashboard** / kasutaja seaded (User settings).
2. Leia **OAuth clients**.
3. Vajuta **Create / New client**.
4. Salvesta:
   - `client_id`
   - `client_secret`

> **Ära jaga** `client_secret`‑i ja **ära commiti** seda Giti!

---

## 3) Repo kloonimine ja failide struktuur

### 3.1 Klooni repo
```bash
git clone https://github.com/sander-rikka/NSO7001_code.git
cd HW1-atmosphere
```

### 3.2 Struktuur
```
copernicus-s5p-python-template/
  README.md
  requirements.txt
  .env.example
  .gitignore
  s5p_workflow.py
  outputs/              # genereeritud failid (tekib jooksutamisel)
```

---

## 4) Python keskkond (virtualenv)

> Virtualenv hoiab sinu projekti paketid eraldi, et miski “ei läheks katki” teiste projektide tõttu.

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Kontroll:
```bash
python -c "import requests, rasterio, matplotlib, docx; print('OK')"
```

---

## 5) Salajaste võtmete seadistamine (ENV muutujad)

Saad valida **2 variandi** vahel.

### Variant A (soovitatud tudengitele): `.env` fail (lihtsam)
1. Tee `.env` fail koopia põhjal:
   ```bash
   cp .env.example .env
   ```
   (Windowsis tee lihtsalt koopia File Exploreris)

2. Ava `.env` ja täida:
   ```
   CDSE_CLIENT_ID=...
   CDSE_CLIENT_SECRET=...
   ```

3. `.env` on `.gitignore` all – see ei lähe repo sisse.


## 6) Ülesande lahendamine (praktiline samm-sammult, vastavalt `air_pollution_s5p.ipynb` töövoole)

Edasi tee töö **märkmikus** `air_pollution_s5p.ipynb`.


Ava fail `air_pollution_s5p.ipynb` ja käivita rakud järjekorras ülevalt alla.

### 6.1 Määra oma parameetrid vastavalt jaotustabelile
- Kasuta tabelist oma kahte tunnust: `VAR1` ja `VAR2`.
- Kasuta tabelist oma aastat: `Year`.
- Soovitus: tee kogu analüüs mõlema tunnuse jaoks eraldi (kaks läbimist).

### 6.2 Määra uuritav ala (bbox)
Märkmikus on vaikimisi Mandri-Euroopa piirdekast:
```python
bbox = BBox([-12.30, 34.59, 32.52, 63.15], crs=CRS.WGS84).transform(CRS(3857))
```
Võid selle jätta samaks või valida väiksema ala, kui tahad kiiremat jooksutamist.

### 6.3 Määra toorandmete päring (Processing API)
Esimeses evalscriptis:
- asenda sisendbänd oma tunnusega (nt `NO2`, `O3`, `CO` või `CH4`);
- sea `time_interval` vastavalt oma aastale (näiteks `"2023-01-01"` kuni `"2023-01-03"`).

Selle sammu eesmärk on saada **ruumiline ülevaade** ühest lühikesest perioodist.

### 6.4 Arvuta kuu keskmine pilves
Järgmises osas (`Mean over period`):
- kasuta `mosaicking: "ORBIT"`;
- hoia sisendis `dataMask`;
- sea kuu vahemik oma aastast (nt `"2023-12-01"` kuni `"2024-01-01"` või mõni muu kuu sinu aastast);
- asenda evalscriptis kasutatav tunnus oma tunnusega.

See samm annab terviklikuma pildi kui üksik ülelend.

### 6.5 Võrdle riike
Plokis `Third part: concentrations by countries`:
- rasterdatakse riikide geomeetriad;
- arvutatakse riigipõhised keskmised (`countries["mean"]`);
- kuvatakse suurimate keskmistega riigid;
- joonistatakse top-riikide boxplot.

Selles osas kommenteeri, millistes riikides on keskmised kõrgemad ja kui suur on hajuvus.

### 6.6 Koosta pealinnade ajasari (Statistical API)
Plokis `Forth part: time series over cities`:
- kasuta `evalscript_stat` skripti;
- sea `time_interval` tervele oma aastale (nt `"2023-01-01"` kuni `"2023-12-31"`);
- kasuta `aggregation_interval="P1D"` (päevane);
- asenda tunnus oma tunnusega ka Statistical API evalscriptis.

Märkmik loeb pealinnad failist `./data/eu_capitals.geojson`, teeb päringud paralleelselt ja koostab tabeli.

### 6.7 Salvesta tulemused
Märkmik salvestab ajarea CSV kujul:
- `./outputs/no2_capitals_timeseries.csv`

Kui analüüsid muud tunnust, salvesta fail ümber sisukama nimega, näiteks:
- `./outputs/o3_capitals_timeseries.csv`
- `./outputs/ch4_capitals_timeseries.csv`
- `./outputs/co_capitals_timeseries.csv`

---

## 7) Mida esitada (kodutöö väljund)

Esita mõlema sinu tunnuse kohta:
- 1 toorvaade kaart (Processing API, lühike periood);
- 1 kuu keskmise kaart (ORBIT + dataMask);
- riikide võrdlus (top keskmised + boxplot);
- pealinnade ajaseeria (Statistical API);
- vähemalt üks CSV ajareaga `outputs/` kaustast.

Kirjalikus osas selgita lühidalt:
- milline oli kasutatud aasta ja ajavahemikud;
- millised piirkonnad/riigid paistsid kõrgete väärtustega;
- kuidas tulemused muutusid tunnuste lõikes.

---

## 8) Tüüpilised vead ja lahendused

### “401 Unauthorized” / “invalid_client”
- Vale `client_id` või `client_secret`.
- Kontrolli, et `.env` on olemas ja väärtused õiged.

### “403 Forbidden”
- OAuth klient või konto õigused pole korrektsed/aktiivsed.
- Loo CDSE töölaual uus OAuth klient ja proovi uuesti.

### “ModuleNotFoundError”
- Virtualenv pole aktiveeritud.
- Paigalda sõltuvused uuesti: `pip install -r requirements.txt`.

### Tulemuses on palju `NaN` väärtusi
- Kontrolli ajavahemikku ja tunnust.
- Kontrolli, et `dataMask` kasutus oleks evalscriptis alles.
- Proovi teist kuud või suuremat ala.

### Statistical API tabel tuleb tühi
- Kontrolli, et `time_interval` poleks väljaspool andmete kättesaadavust.
- Kontrolli, et `geometry` CRS oleks korrektne (`CRS(capitals.crs)`).

---

## 9) Hea tava (Git ja turvalisus)

- `client_secret` ei tohi minna reposti.
- `.env` peab jääma `.gitignore` alla.
- `outputs/` tulemusi ei pea repoga kaasa panema.
- Hoia failinimed üheselt mõistetavad (tunnus + aasta), et hindamisel oleks lihtne jälgida.

---

