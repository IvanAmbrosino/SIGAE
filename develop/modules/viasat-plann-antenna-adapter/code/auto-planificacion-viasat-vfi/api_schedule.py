#!/usr/bin/python3.10
from datetime import datetime, timedelta
from flask import Flask, request
from cgssdbops import cgss_db_ops
from json import load, dumps
from flask_restful import Resource, Api
app = Flask(__name__)
api = Api(app)

class Antenna_Schedule(Resource):
    """Get antennas per activities"""
    
    def __load_config(self):        
        """Load config file"""
        with open("configurations/configuration.json", 'r', encoding='utf-8') as fp:
            data = load(fp)
            return data['Antenna_Schedule']

    def query_formatted_time(self, offset):
        """Datetime formated as required in the 
        CGSS Planning DBs"""
        return (datetime.utcnow()+timedelta(hours=offset)).strftime("%Y-%m-%d %H:%M:%S.000")

    def return_formatted_time(self, db_time):
        """Datetime 2 time format defined in VFI Viasat doc."""
        return db_time.isoformat()

    def is_the_unit(self, cur, data, oid):
        """Return antena id"""
        unit_id = cgss_db_ops.query_conf(cur, data["db"], 
                                            data["table"][1], oid)[0][data["table"][2]]
        if (cgss_db_ops.get_unit_by_id(cur, data["db"],
                                       data["table"][2],unit_id)["nombre"] == self.unit_name):
            return True
        else:
            return False

    def get_activities4unit(self, bbdd, plan):
        """Traigo las pasadas de la DB y las itero."""
        conn, cur = cgss_db_ops.open_db_conn(bbdd["host"], bbdd["user"], bbdd["passwd"], plan['db'])
        activities = cgss_db_ops.query_plan(cur, self.query_formatted_time(-0.25),
                                            self.query_formatted_time(72),
                                          plan["db"], plan["table"][0])
        # Itero y almaceno en una lista las actividades que corresponden a la antena.
        activities_2_schedule = dict()
        i=0
        for activity in activities:
            if self.is_the_unit(cur, plan, activity["idMacro"]):
                activity['Satelite'] = cgss_db_ops.transform_norad2satname(
                    cur, activity['Satelite'], plan['db'], plan['table'][3])['Descripcion']
                activity['FechaHoraInicial'] = self.return_formatted_time(activity['FechaHoraInicial'])
                activity['FechaHoraFinal'] = self.return_formatted_time(activity['FechaHoraFinal'])
                activities_2_schedule[i]=activity
                i+=1
        cgss_db_ops.close_db_conn(conn)
        #print("DUMPS: ",dumps(activities_2_schedule))
        return activities_2_schedule

    def get(self, unit):
        """Consulta las actividades para la estacion."""
        data = self.__load_config()
        print("UNIT: ",unit)
        self.unit_name = unit
        #self.unit_name = request.args.get("antena")
        print(self.get_activities4unit(data["bbdd"], data["Plan"]))
        return self.get_activities4unit(data["bbdd"], data["Plan"])
        #return {"data":"ANTENA 6.1"}

api.add_resource(Antenna_Schedule, '/API_Schedule/<string:unit>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
