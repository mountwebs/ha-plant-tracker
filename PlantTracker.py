import appdaemon.plugins.hass.hassapi as hass
import datetime
import json


class PlantTracker(hass.Hass):
    def initialize(self):
        self.initialize_plants()
        runtime = datetime.time(1, 19)
        self.run_daily(self.recalculate_all_states, runtime)
        for plant in self.args["plants"]:
            entity = "plant_tracker.{}".format(plant.replace(" ", "_"))
            self.listen_state(self.recalculate_state,
                              entity,
                              attribute="last_watered")

    def get_plants_from_db(self):
        #try:
        with open(self.args["file"], 'r') as f:
            db_plants = json.load(f)
        if db_plants:
            return db_plants
        else:
            db_plants = {}
            return db_plants
        #except:
        #    self.log("Could not load db")
        #    return {}

    def save_plants_to_db(self, db_plants):
        try:
            with open(self.args["file"], 'w') as f:
                json.dump(db_plants, f, sort_keys=True, indent=4)
        except:
            self.log("Could not save to db")

    def initialize_plants(self):
        if "plants" not in self.args:
            self.log("No plants in yaml")
            return

        yaml_plants = self.args["plants"]
        db_plants = self.get_plants_from_db()
        for plant in yaml_plants.items():
            entity_name, plant_attr = plant
            entity = "plant_tracker.{}".format(entity_name.replace(" ", "_"))

            if "watering_interval" not in plant_attr:
                self.log("No watering interval for {}".format(entity_name))
                self.log("Initialization failed for {}".format(entity_name))
                continue
            if entity in db_plants:
                plant_attr["last_watered"] = db_plants[entity]
                last_watered = db_plants[entity]
            else:
                if "last_watered" in plant_attr:
                    last_watered = plant_attr["last_watered"]
                else:
                    today = datetime.datetime.now().date()
                    today = today.strftime("%Y/%m/%d")
                    last_watered = today

            if "watering_window" in plant_attr:
                watering_window = plant_attr["watering_window"]
            else:
                watering_window = 1

            new_state, days_since_watered = self.calculate(plant_attr["watering_interval"], last_watered,
                                                           watering_window)
            plant_attr["last_watered"] = last_watered
            plant_attr["days_since_watered"] = days_since_watered

            if "icon" not in plant_attr:
                plant_attr["icon"] = "mdi:flower"

            self.set_state(entity, state=new_state, attributes=plant_attr)
            self.log("Initialized : {}".format(plant))

    def calculate(self, watering_interval, last_watered_str, watering_window):
        today = datetime.datetime.now().date()

        dateSplit = last_watered_str.split("/")
        dateYear = int(dateSplit[0])
        dateMonth = int(dateSplit[1])
        dateDay = int(dateSplit[2])

        last_watered = datetime.date(dateYear, dateMonth, dateDay)
        days_since_watered = today - last_watered
        if days_since_watered.days == 0:
            new_state = 3
        elif days_since_watered.days < watering_interval:
            new_state = 2
        elif days_since_watered.days <= watering_interval + watering_window - 1:
            new_state = 1
        else:
            new_state = 0

        days_since_watered_int = days_since_watered.days

        return new_state, days_since_watered_int

    def recalculate_state(self, entity, attribute, old, new, kwargs):
        plant_info = self.get_state(entity, attribute="all")
        plant_attr = plant_info["attributes"]
        watering_interval = plant_attr["watering_interval"]
        if "watering_window" in plant_attr:
            watering_window = plant_attr["watering_window"]
        else:
            watering_window = 1
        new_state, days_since_watered = self.calculate(watering_interval, new, watering_window)

        plant_attr["days_since_watered"] = days_since_watered
        self.set_state(entity, state=new_state, attributes=plant_attr)
        self.log("Set state for {} to {}".format(entity, new_state))

        db_plants = self.get_plants_from_db()
        db_plants[entity] = new

        self.save_plants_to_db(db_plants)

        self.log("Saved state to db")

    def recalculate_all_states(self, kwargs):
        plants = self.args["plants"]
        for plant in plants:
            entity = "plant_tracker.{}".format(plant.replace(" ", "_"))

            if self.get_state(entity) != None and self.get_state(entity, attribute="last_watered") != None:
                plant_info = self.get_state(entity, attribute="all")
                plant_attr = plant_info["attributes"]
                watering_interval = plant_attr["watering_interval"]
                if "watering_window" in plant_info:
                    watering_window = plant_info["watering_window"]
                else:
                    watering_window = 1

                last_watered = plant_attr["last_watered"]

                new_state, days_since_watered = self.calculate(watering_interval, last_watered, watering_window = watering_window)
                plant_attr["days_since_watered"] = days_since_watered
                self.set_state(entity, state=new_state, attributes=plant_attr)

                self.log("Recalculated stated for {}".format(entity))
