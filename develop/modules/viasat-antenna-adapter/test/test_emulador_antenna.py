import os
import time
import shutil
import datetime

# Configuración
DIRECTORIO_ENTRADA = "/home/soporte/etc/remote"
DIRECTORIO_SALIDA = "/home/soporte/etc/remote/archive"
INTERVALO = 2  # segundos

# Contenido XML a insertar
XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<EphemImport xmlns="$VFIROOT/etc/import.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="$VFIROOT/etc/import.xsd /home/scc/etc/Import.xsd">
\t<TimeTag>2025 195 12:22:50</TimeTag>
\t<Status>ACCEPTED</Status>
</EphemImport>
"""

def procesar_archivos():
    for file in os.listdir(DIRECTORIO_ENTRADA):
        if file.startswith("rciEphem_") and file.endswith(".done"):
            base_name = file.replace(".done", "")
            archivo_rci = os.path.join(DIRECTORIO_ENTRADA, base_name)
            archivo_rci_done = os.path.join(DIRECTORIO_ENTRADA, file)

            if os.path.exists(archivo_rci):
                suffix = base_name.split("rciEphem_")[1]
                archivo_import = f"importSched_{suffix}"
                archivo_import_done = f"importSched_{suffix}.done"

                # Mover archivos a archive y renombrar + fecha
                shutil.move(archivo_rci, os.path.join(DIRECTORIO_SALIDA, f"{base_name}_{datetime.datetime.now().strftime('%Y_%j_%H%M%S')}"))
                shutil.move(archivo_rci_done, os.path.join(DIRECTORIO_SALIDA, file))

                # Rutas de archivos import
                destino_rci = os.path.join(DIRECTORIO_ENTRADA, archivo_import)
                destino_done = os.path.join(DIRECTORIO_ENTRADA, archivo_import_done)

                # Crear archivos Import y escribir XML dentro del nuevo archivo
                with open(destino_rci, "w", encoding="utf-8") as f:
                    f.write(XML_CONTENT)
                with open(destino_done, "w", encoding="utf-8") as _:
                    pass

                print(f"[INFO] Procesado: {archivo_rci} y {archivo_rci_done}")

if __name__ == "__main__":
    print("Escuchando archivos nuevos...")
    while True:
        procesar_archivos()
        time.sleep(INTERVALO)
