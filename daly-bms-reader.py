import dalybms
from paho.mqtt.enums import MQTTProtocolVersion
import paho.mqtt.publish as publish
from time import sleep
import json


mqtt_topic = "energy/battery/pack1/cellvoltages"


# Connects to RS485 via USB, gets all voltages and disconnects again
def get_actual_cell_voltages():
    new_device = dalybms.DalyBMS()
    new_device.connect('/dev/ttyUSB0')
    cell_voltages = new_device.get_cell_voltages()
    new_device.disconnect()
    return cell_voltages


# Parses array for highest cell voltage
def get_max_cell_voltage(cell_voltages_data):
    list_of_voltages = []
    for each in cell_voltages_data:
        list_of_voltages.append(cell_voltages_data[each])
    return max(list_of_voltages)


# Parses array for lowest cell voltage
def get_min_cell_voltage(cell_voltages_data):
    list_of_voltages = []
    for each in cell_voltages_data:
        list_of_voltages.append(cell_voltages_data[each])
    return min(list_of_voltages)


# Prepares topic data and publishes all at once to MQTT
def publish_cell_voltages_to_mqtt(cell_voltages_data):
    msgs = []
    for each in cell_voltages_data:
        msgs.append((("{}/{}".format(mqtt_topic, each), cell_voltages_data[each], 0, False)))
    msgs.append(("{}/min".format(mqtt_topic), get_min_cell_voltage(cell_voltages_data), 0, False))
    msgs.append(("{}/max".format(mqtt_topic), get_max_cell_voltage(cell_voltages_data), 0, False))
    # print(msgs)
    publish.multiple(msgs, hostname="192.168.1.15", protocol=MQTTProtocolVersion.MQTTv5)


# Configure Home Assistant to auto-detect the incoming data
def configure_homeassistant():
    discovery_prefix = "homeassistant"
    device = {
        "identifiers": ["pack1"],
        "name": "Battery Pack 1",
        "model": "LiFePO4 8s2p",
        "manufacturer": "Wings of Future"
    }

    msgs = []

    # loop for cell 1-8
    for x in range(1, 9):
        object_id = f"pack1_cell{x}"
        config_topic = f"{discovery_prefix}/sensor/{object_id}/config"
        payload = {
            "name": f"Cell {x} Voltage",
            "state_topic": f"{mqtt_topic}/{x}",
            "unit_of_measurement": "V",
            "device_class": "voltage",
            "unique_id": f"{object_id}_voltage",
            "device": device
        }
        msgs.append((config_topic, json.dumps(payload), 0, True))

    # set for min
    config_topic = f"{discovery_prefix}/sensor/pack1_cellmin/config"
    payload = {
        "name": "Cell Min Voltage",
        "state_topic": f"{mqtt_topic}/min",
        "unit_of_measurement": "V",
        "device_class": "voltage",
        "unique_id": "pack1_cellmin_voltage",
        "device": device
    }
    msgs.append((config_topic, json.dumps(payload), 0, True))

    # set for max
    config_topic = f"{discovery_prefix}/sensor/pack1_cellmax/config"
    payload = {
        "name": "Cell Max Voltage",
        "state_topic": f"{mqtt_topic}/max",
        "unit_of_measurement": "V",
        "device_class": "voltage",
        "unique_id": "pack1_cellmax_voltage",
        "device": device
    }
    msgs.append((config_topic, json.dumps(payload), 0, True))

    # print(msgs)

    publish.multiple(msgs, hostname="192.168.1.15", protocol=MQTTProtocolVersion.MQTTv5)




# Run once per boot only
configure_homeassistant()

# Continuous loop that will never break.
while True:
    try:
        myVoltages = get_actual_cell_voltages()
        publish_cell_voltages_to_mqtt(myVoltages)
        sleep(5)
    except Exception as e:
        print("ERROR: {}".format(e))
    sleep(0.5)
