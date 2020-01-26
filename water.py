entity = data.get('entity')

today = datetime.datetime.now().date()
today_str = "{}/{}/{}".format(today.year, today.month, today.day)

attr = hass.states.get(entity).attributes.copy()

attr["last_watered"] = today_str

hass.states.set(entity , 3, attr)
