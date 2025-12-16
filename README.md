# SOSI Import (QGIS plugin)

QGIS-plugin for å åpne SOSI-filer raskt i QGIS, og/eller konvertere SOSI til GeoPackage.

## Funksjoner

- **Rask åpning**: legger SOSI-lag direkte inn i QGIS (hurtig for store filer)
- **Konverter til GeoPackage (rask)**: konverterer med `ogr2ogr` og legger lagene inn i prosjektet

> Merk: Ved “rask” GeoPackage-konvertering bygges **spatial index ikke under import** for ytelse.
> Du kan bygge spatial index senere i QGIS ved behov.

## Krav

- QGIS >= 3.22 (testet på QGIS 3.40.x)
- GDAL/OGR følger med QGIS (pluginen bruker `ogr2ogr` fra QGIS-installasjonen)

## Installering (fra ZIP)

1. Last ned plugin-zip (`sosi2gpkg_*.zip`)
2. QGIS: **Plugins → Manage and Install Plugins… → Install from ZIP**
3. Velg zip-fila

## Bruk

1. Klikk plugin-ikonet i verktøylinjen (Kartverket)
2. Velg SOSI-fil
3. Velg:
   - **Rask åpning**, eller
   - **Konverter til GeoPackage**

## Bygge spatial index etterpå (anbefalt ved store lag)

- Åpne **Processing Toolbox**
- Kjør **Create spatial index** på lag i GeoPackage

## Utvikling

Repoet inneholder plugin-mappa `sosi2gpkg/`. Når du lager ZIP for QGIS må `sosi2gpkg/` ligge på toppnivå i zip-en.

## Lisens

Se `LICENSE`.

## Feil og ønsker

Legg inn issues i GitHub:

- https://github.com/tompreik-kv/sosi2gpkg/issues
