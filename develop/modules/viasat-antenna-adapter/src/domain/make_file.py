"""Creating TLE or Plann files to send to the antenna"""
import subprocess
import os
from abc import ABC, abstractmethod
from lxml import etree

from infraestructure.config_manager import ConfigManager

class MakeFile(ABC):
    """Abstract class to define the make-file strategy"""

    @abstractmethod
    def make_file_to_send(self, content: list[dict]) -> bool:
        """Creates the file to be sent to the antenna"""

    @abstractmethod
    def remove_tmp_files(self, path: str) -> bool:
        """Delete a tmp file"""


class MakeTLEFile(MakeFile):
    """Class that creates the TLE file to be sent to the antenna"""
    def __init__(self):
        self.tmp_path = '/app/tmp/tmp_file.txt'
        self.header = "n\n"

    def make_file_to_send(self, content: list[dict]) -> bool:
        """
        Creates the TLE file to be sent to the antennas.
        Receives a list of TLEs and make the file.
        """
        tle_string = self.header # Inicializa el string con el header
        content = self.traduce_sat_name([content])
        with open(self.tmp_path, "w", encoding='utf-8') as tle_file:
            for tle in content:
                tle_string += "\n".join([tle["satellite_name"],tle["line1"],tle["line2"]]) + "\n"
            tle_file.write(tle_string)
        subprocess.run(["unix2dos", self.tmp_path], check=True) # Se convierte en formato DOS

        # Arma el archivo .done
        with open(f"{self.tmp_path}.done", 'w',encoding='utf-8') as _:
            pass

        return True

    def traduce_sat_name(self, content: list[dict]) -> list[dict]:
        """Realiza la traduccion del nombre del satelite a uno que pueda interpretar la antena"""
        return_list = []
        list_translation = ConfigManager().load_translation_config()
        for tle in content:
            for name, altname in list_translation:
                if tle['satellite_name'] == name:
                    tle['satellite_name'] = altname
            return_list.append(tle)
        return return_list

    def remove_tmp_files(self, path: str = '/app/tmp/') -> bool:
        """Remove all tmp files"""
        if not os.path.isdir(path):
            print(f"[ERROR] La ruta {path} no es un directorio válido.")
            return

        archivos = os.listdir(path)
        if not archivos:
            print(f"[INFO] El directorio {path} está vacío.")
            return

        for archivo in archivos:
            archivo_path = os.path.join(path, archivo)
            try:
                if os.path.isfile(archivo_path):
                    os.remove(archivo_path)
                    print(f"[OK] Archivo eliminado: {archivo_path}")
                else:
                    print(f"[SKIP] No es un archivo (quizás directorio): {archivo_path}")
            except Exception as e: # pylint: disable=broad-exception-caught
                print(f"[ERROR] No se pudo eliminar {archivo_path}: {e}")

class MakePlannFile(MakeFile):
    """Class that creates the Planning file to be sent to the antenna"""
    def __init__(self):
        self.tmp_path = '/app/tmp/tmp_file.xml'

    def build_schedule_xml(self, tasks):
        """Builds an XML document for the remote schedule based on the provided tasks."""
        nsmap = {
            None: "$VFIROOT/etc/schedule.xsd",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }
        root = etree.Element("RemoteSchedule", nsmap=nsmap)
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                "$VFIROOT/etc/schedule.xsd")

        for task in tasks:
            task_node = etree.SubElement(root, "Task")
            etree.SubElement(task_node, "Action").text = task["action"]

            if "task_id" in task:
                etree.SubElement(task_node, "TaskID").text = task["task_id"]

            if task["action"] == "ADD":
                track = etree.SubElement(task_node, "Track")
                etree.SubElement(track, "Satellite").text = task["satellite"]
                etree.SubElement(track, "ConfigID").text = str(task["config_id"])
                etree.SubElement(track, "AntennaID").text = task["antenna_id"]
                etree.SubElement(track, "StartTime").text = task["start"]
                etree.SubElement(track, "EndTime").text = task["end"]
                if "prepass" in task:
                    prepass = etree.SubElement(track, "PrePass")
                    start_offset = etree.SubElement(prepass, "StartOffsetTime")
                    start_offset.text = str(task.get("prepass", str(task["postpass"])))
                if "postpass" in task:
                    postpass = etree.SubElement(track, "PostPass")
                    etree.SubElement(postpass, "Enabled").text = "Yes"
                    etree.SubElement(postpass, "Duration").text = str(task["postpass"])

        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def make_file_to_send(self, content: list[dict]) -> bool:
        """
        Creates the Planning file to be sent to the antennas.
        Receives a list of Tasks and make the file.
        """
        xml_content = self.build_schedule_xml(content)
        with open(self.tmp_path, "w", encoding='utf-8') as tle_file:
            tle_file.write(xml_content)
        subprocess.run(["unix2dos", self.tmp_path], check=True) # Se convierte en formato DOS

        # Arma el archivo .done
        with open(f"{self.tmp_path}.done", 'w',encoding='utf-8') as _:
            pass

        return True

    def remove_tmp_files(self, path: str = '/app/tmp/') -> bool:
        """Remove all tmp files"""
        if not os.path.isdir(path):
            print(f"[ERROR] La ruta {path} no es un directorio válido.")
            return

        archivos = os.listdir(path)
        if not archivos:
            print(f"[INFO] El directorio {path} está vacío.")
            return

        for archivo in archivos:
            archivo_path = os.path.join(path, archivo)
            try:
                if os.path.isfile(archivo_path):
                    os.remove(archivo_path)
                    print(f"[OK] Archivo eliminado: {archivo_path}")
                else:
                    print(f"[SKIP] No es un archivo (quizás directorio): {archivo_path}")
            except Exception as e: # pylint: disable=broad-exception-caught
                print(f"[ERROR] No se pudo eliminar {archivo_path}: {e}")
