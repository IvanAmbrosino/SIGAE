"""Module for Viasat Antenna Adapter."""
from lxml import etree

def build_schedule_xml(tasks):
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
        etree.SubElement(task_node, "TaskID").text = task["task_id"]
        etree.SubElement(task_node, "Action").text = task["action"]

        if task["action"] == "ADD":
            track = etree.SubElement(task_node, "Track")
            etree.SubElement(track, "Satellite").text = task["satellite"]
            etree.SubElement(track, "ConfigID").text = str(task["config_id"])
            etree.SubElement(track, "AntennaID").text = task["antenna_id"]
            etree.SubElement(track, "StartTime").text = task["start"]
            etree.SubElement(track, "EndTime").text = task["end"]
            etree.SubElement(track, "PrePass").append(
                etree.Element("StartOffsetTime", text=str(task.get("prepass", 120)))
            )

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
