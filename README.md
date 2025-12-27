# SOSI Import (QGIS plugin)

QGIS-plugin for å importere SOSI og konvertere til GeoPackage (GPKG). Resultatet lastes automatisk inn i prosjektet.

## Funksjoner

- **Importer SOSI → GeoPackage**: konverterer med `ogr2ogr` og legger alle lag inn i QGIS-prosjektet
- **Støtte for ukjent/manglende KOORDSYS**: dersom `KOORDSYS` mangler eller er ukjent (f.eks. `99`), får du en dialog der du kan velge riktig input-CRS og eventuelt transformere til en annen CRS

> Merk: Under import bygges **spatial index ikke** for ytelse.
> Bygg spatial index senere i QGIS ved behov.

## Krav

- QGIS >= 3.22
- Testet på:
  - QGIS 3.40.x (Qt5)
  - QGIS 3.44.6 (Qt 6.8.1)
- GDAL/OGR følger med QGIS (pluginen bruker `ogr2ogr` fra QGIS-installasjonen)

## Installering (fra ZIP)

1. Last ned plugin-zip (`sosi2gpkg_*.zip`)
2. QGIS: **Plugins → Manage and Install Plugins… → Install from ZIP**
3. Velg zip-fila

## Bruk

1. Klikk plugin-ikonet i verktøylinjen (Kartverket)
2. Velg **SOSI innfil** og **GPKG utfil**
3. Trykk **Importer**
4. Hvis `KOORDSYS` er ukjent/mangler: velg riktig **Input CRS** (påkrevd) og eventuell **Output CRS**

## Bygge spatial index etterpå (anbefalt ved store lag)

- Åpne **Processing Toolbox**
- Kjør **Create spatial index** på lagene i GeoPackage

## Utvikling

Repoet inneholder plugin-mappa `sosi2gpkg/`. Når du lager ZIP for QGIS må `sosi2gpkg/` ligge på toppnivå i zip-en.

## Lisens

Se `LICENSE`.

## Feil og ønsker

Legg inn issues i GitHub:

- https://github.com/tompreik-kv/sosi2gpkg/issues
