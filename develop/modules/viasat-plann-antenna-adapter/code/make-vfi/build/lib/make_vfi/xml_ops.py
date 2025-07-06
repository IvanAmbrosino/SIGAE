#!/usr/bin/python3
from datetime import datetime, timezone
import xml.etree.cElementTree as ET
import xml.dom.minidom

class OpsOverXML():
    """Crea el XML rciSched"""
    def create_root(self):
        """Inicia el documento."""
        root = ET.Element("RemoteSchedule")
        root.set('xmlns', "$VFIROOT/etc/schedule.xsd")
        root.set('xmlns:xsi',"http://www.w3.org/2001/XMLSchema-instance")
        root.set('xsi:schemaLocation',"$VFIROOT/etc/schedule.xsd")
        return root

    def write_file(self, root, filename, path):
        """Escribe el archivo de salida Schedule"""        
        dom = xml.dom.minidom.parseString(ET.tostring(root))
        xml_string = dom.toprettyxml()
        part1, part2 = xml_string.split('?>')
        with open(filename, mode='w',encoding='utf-8') as schedule:
            schedule.write(part1 + 'encoding=\"{}\"?>\n'.format('UTF-8') + part2)
            schedule.close()
        return True

    def add_task(self, root, activities, unit):
        """Agrega las tareas en base a las activities"""
        for activity in activities:
            # Convierto el tiempo para el formato correspondiente
            try:
                aos = datetime.strptime(activities[activity]['FechaHoraInicial'],
                                        '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y %j %H:%M:%S')
            except ValueError:
                aos = datetime.strptime(activities[activity]['FechaHoraInicial'],
                                        '%Y-%m-%dT%H:%M:%S').strftime('%Y %j %H:%M:%S')
            try:
                los = datetime.strptime(activities[activity]['FechaHoraFinal'],
                                    '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y %j %H:%M:%S')
            except ValueError:
                los = datetime.strptime(activities[activity]['FechaHoraFinal'],
                                    '%Y-%m-%dT%H:%M:%S').strftime('%Y %j %H:%M:%S')
            doc = ET.SubElement(root, "Task")
            ET.SubElement(doc, "TaskID").text = f"{activities[activity]['Satelite']}_{unit}_{aos[0:8]}"
            ET.SubElement(doc, "Action").text = "ADD"
            activity_data = ET.SubElement(doc, "Track")
            ET.SubElement(activity_data, "Satellite").text = activities[activity]['Satelite']
            ET.SubElement(activity_data, "ConfigID").text = "10"
            ET.SubElement(activity_data, "StartTime").text = aos
            ET.SubElement(activity_data, "EndTime").text = los
            prepass = ET.SubElement(activity_data, "PrePass")
            ET.SubElement(prepass, "StartOffsetTime").text = "120"
        return root

    def __init__(self) -> None:
        pass
