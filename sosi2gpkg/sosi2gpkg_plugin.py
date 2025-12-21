from qgis.PyQt.QtCore import QCoreApplication, QProcess
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QProgressDialog, QApplication
from qgis.core import QgsProject, QgsVectorLayer, QgsApplication
import os
import shutil
import tempfile
from pathlib import Path
import codecs
import re


class Sosi2GpkgPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.toolbar = None

    def tr(self, text):
        return QCoreApplication.translate("Sosi2GpkgPlugin", text)

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon_sosi2gpkg.svg")
        self.action = QAction(QIcon(icon_path), self.tr("SOSI Import"), self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.tr("&Kartverket"), self.action)
        self.toolbar = self.iface.addToolBar("Kartverket")
        self.toolbar.addAction(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu(self.tr("&Kartverket"), self.action)
            try:
                if self.toolbar:
                    self.toolbar.removeAction(self.action)
            except Exception:
                pass
            self.action = None

    # -------------------------
    # Helpers
    # -------------------------
    def find_ogr2ogr(self) -> str:
        prefix = QgsApplication.prefixPath()
        candidates = [
            os.path.join(prefix, "bin", "ogr2ogr.exe"),
            os.path.join(prefix, "apps", "gdal", "bin", "ogr2ogr.exe"),
            os.path.join(prefix, "bin", "ogr2ogr"),
            os.path.join(prefix, "apps", "gdal", "bin", "ogr2ogr"),
            shutil.which("ogr2ogr"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        raise RuntimeError("Fant ikke ogr2ogr. Sjekk QGIS-installasjonen/OSGeo4W eller PATH.")

    def make_workaround_copy(self, src_path: str, force_45: bool = True, target_encoding: str = "iso-8859-10") -> str:
        """Workaround: bytt ..TEGNSETT og evt ..SOSI-VERSJON, skriv som ISO-8859-10."""
        src = Path(src_path)
        tmpdir = Path(tempfile.mkdtemp(prefix="qgis_sosi_"))
        dst = tmpdir / (src.stem + "_workaround.sos")

        raw = src.read_bytes()
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw[len(codecs.BOM_UTF8):]

        while raw and raw[:1] in b" \t\r\n":
            raw = raw[1:]

        text_lines = raw.decode("utf-8", errors="replace").splitlines(True)

        out_lines = []
        for line in text_lines:
            if line.startswith("..TEGNSETT"):
                out_lines.append("..TEGNSETT ISO8859-10\n")
                continue
            if force_45 and line.startswith("..SOSI-VERSJON"):
                out_lines.append("..SOSI-VERSJON 4.5\n")
                continue
            out_lines.append(line)

        dst.write_text("".join(out_lines), encoding=target_encoding, errors="replace", newline="\n")
        return str(dst)

    def add_all_layers(self, datasource_path: str, progress: QProgressDialog) -> int:
        from osgeo import ogr
        ds = ogr.Open(datasource_path)
        if ds is None:
            raise RuntimeError(f"Klarte ikke å åpne: {datasource_path}")

        layer_count = ds.GetLayerCount()
        if layer_count <= 0:
            return 0

        # Skru av rendering mens vi legger til lag
        canvas = getattr(self.iface, "mapCanvas", None)
        old_render = None
        if canvas:
            old_render = canvas().renderFlag()
            canvas().setRenderFlag(False)

        try:
            progress.setRange(0, layer_count)
            progress.setValue(0)
            added = 0
            for i in range(layer_count):
                if progress.wasCanceled():
                    break
                lyr = ds.GetLayerByIndex(i)
                name = lyr.GetName()
                uri = f"{datasource_path}|layername={name}"
                vl = QgsVectorLayer(uri, name, "ogr")
                if vl.isValid():
                    QgsProject.instance().addMapLayer(vl)
                    added += 1
                progress.setLabelText(self.tr(f"Laster lag: {name} ({i+1}/{layer_count})"))
                progress.setValue(i + 1)
                QApplication.processEvents()
            return added
        finally:
            if canvas and old_render is not None:
                canvas().setRenderFlag(old_render)
                canvas().refresh()

    # -------------------------
    # ogr2ogr runner (progress + cancel + output capture)
    # -------------------------
    def run_ogr2ogr(self, ogr2ogr_path: str, args: list, progress: QProgressDialog, label: str):
        progress.setRange(0, 0)  # busy først
        progress.setValue(0)
        progress.setLabelText(label)
        QApplication.processEvents()

        proc = QProcess()
        proc.setProgram(ogr2ogr_path)
        proc.setArguments(args)
        proc.setProcessChannelMode(QProcess.MergedChannels)

        rx_pct = re.compile(r"(\d{1,3})\s*%")
        rx_dots = re.compile(r"(?:^|\s)(\d{1,3})(?=\.+)")
        got_determinate = False
        last_val = -1

        out_all = ""

        proc.start()
        if not proc.waitForStarted(5000):
            raise RuntimeError("Klarte ikke å starte ogr2ogr-prosessen.")

        while True:
            QApplication.processEvents()

            if progress.wasCanceled():
                proc.kill()
                proc.waitForFinished(2000)
                raise RuntimeError("Avbrutt av bruker.")

            if proc.waitForReadyRead(50):
                chunk = bytes(proc.readAll()).decode("utf-8", errors="replace")
                out_all += chunk

                for line in re.split(r"[\r\n]+", chunk):
                    line = line.strip()
                    if not line:
                        continue

                    m = rx_pct.search(line)
                    val = None
                    if m:
                        val = max(0, min(100, int(m.group(1))))
                    else:
                        hits = rx_dots.findall(line)
                        if hits:
                            try:
                                val = max(0, min(100, int(hits[-1])))
                            except Exception:
                                val = None

                    if val is not None:
                        if not got_determinate:
                            progress.setRange(0, 100)
                            got_determinate = True
                        if val != last_val:
                            last_val = val
                            progress.setValue(val)
                            progress.setLabelText(self.tr(f"{label} ({val}%)"))
                    else:
                        if not got_determinate:
                            progress.setLabelText(self.tr(label))

            if proc.state() == QProcess.NotRunning:
                break

        rest = bytes(proc.readAll()).decode("utf-8", errors="replace")
        if rest:
            out_all += rest

        exit_code = proc.exitCode()
        if exit_code != 0:
            msg = out_all.strip() or "(ingen output fra ogr2ogr)"
            raise RuntimeError(f"ogr2ogr feilet (exit code {exit_code}).\n\nOutput:\n{msg}")

        progress.setRange(0, 100)
        progress.setValue(100)
        QApplication.processEvents()
        return out_all

    # -------------------------
    # Converter: GeoPackage (fast + robust fallback)
    # -------------------------
    def convert_gpkg(self, in_sos: str, out_gpkg: str, progress: QProgressDialog):
        """Rask konvertering først (-gt, ingen -skipfailures). Fallback til robust (-skipfailures, ingen -gt)."""
        ogr2ogr_path = self.find_ogr2ogr()

        if os.path.exists(out_gpkg):
            try:
                os.remove(out_gpkg)
            except Exception:
                pass

        base_args = [
            "--config", "OGR_SQLITE_SYNCHRONOUS", "OFF",
            "--config", "OGR_SQLITE_JOURNAL_MODE", "MEMORY",
            # SPATIAL_INDEX=NO for fart. Bygg spatial index senere hvis ønskelig.
            "-lco", "SPATIAL_INDEX=NO",
            "-nlt", "PROMOTE_TO_MULTI",
            "-progress",
        ]

        fast_args = ["-f", "GPKG", out_gpkg, in_sos, "-gt", "50000"] + base_args

        try:
            self.run_ogr2ogr(ogr2ogr_path, fast_args, progress, self.tr("Konverterer til GeoPackage (rask)"))
            return "fast"
        except Exception:
            # robust fallback
            if os.path.exists(out_gpkg):
                try:
                    os.remove(out_gpkg)
                except Exception:
                    pass
            robust_args = ["-f", "GPKG", out_gpkg, in_sos, "-skipfailures"] + base_args
            self.run_ogr2ogr(ogr2ogr_path, robust_args, progress, self.tr("Konverterer til GeoPackage (robust)"))
            return "robust"

    # -------------------------
    # Main UI (kun konvertering)
    # -------------------------
    def run(self):
        try:
            from osgeo import ogr  # noqa
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), self.tr("SOSI Import"), str(e))
            return

        in_sos, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            self.tr("Velg SOSI-fil"),
            "",
            "SOSI (*.sos *.SOS);;Alle filer (*.*)"
        )
        if not in_sos:
            return
        in_sos = os.path.normpath(in_sos)

        # --- CONVERT to GPKG ---
        suggested = str(Path(in_sos).with_suffix(".gpkg"))
        out_gpkg, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(), self.tr("Lagre GeoPackage som"), suggested, "GeoPackage (*.gpkg)"
        )
        if not out_gpkg:
            return
        out_gpkg = os.path.normpath(out_gpkg)
        if not out_gpkg.lower().endswith(".gpkg"):
            out_gpkg += ".gpkg"

        if os.path.exists(out_gpkg):
            reply = QMessageBox.question(
                self.iface.mainWindow(), self.tr("Overskriv fil?"),
                self.tr("Filen finnes allerede:\n{0}\n\nVil du overskrive?").format(out_gpkg),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        progress = QProgressDialog(self.tr("Starter…"), self.tr("Avbryt"), 0, 0, self.iface.mainWindow())
        progress.setWindowTitle(self.tr("Kartverket – SOSI"))
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        try:
            # Først prøv direkte konvertering
            try:
                mode = self.convert_gpkg(in_sos, out_gpkg, progress)
            except Exception:
                progress.setLabelText(self.tr("Direkte konvertering feilet – prøver workaround…"))
                QApplication.processEvents()
                workaround = self.make_workaround_copy(in_sos, force_45=True, target_encoding="iso-8859-10")
                mode = self.convert_gpkg(workaround, out_gpkg, progress)

            if progress.wasCanceled():
                progress.close()
                return

            progress.setLabelText(self.tr("Konvertert. Laster lag i QGIS…"))
            QApplication.processEvents()
            added = self.add_all_layers(out_gpkg, progress)

            progress.close()
            QMessageBox.information(
                self.iface.mainWindow(), self.tr("SOSI Import – konvertert"),
                self.tr(
                    "Lagret:\n{0}\n\nLa til {1} lag i prosjektet.\n\n"
                    "Merk: Spatial index ble ikke bygget under import (for fart). "
                    "Bygg den senere ved behov (Processing → 'Create spatial index')."
                ).format(out_gpkg, added)
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(self.iface.mainWindow(), self.tr("SOSI Import – konverter"), str(e))
