import asyncio
import logging
import json
import paho.mqtt.client as mqtt
from pymodbus.client import AsyncModbusTcpClient

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
log = logging.getLogger("EdgeGateway")

# MQTT Configuration
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "factory/motor/telemetry"

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info(f"[+] Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        log.error(f"[!] Failed to connect to MQTT Broker, return code {rc}")

async def poll_plc():
    log.info("[*] Initializing Edge Gateway...")
    
    # Setup MQTT Client (paho-mqtt v1.6.x style)
    mqtt_client = mqtt.Client(client_id="EdgeGateway_01")
    mqtt_client.on_connect = on_mqtt_connect
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() # Start background thread for MQTT network traffic
    except Exception as e:
        log.error(f"[!] MQTT Connection Error: {e}")
        return

    # Setup Modbus Client
    modbus_client = AsyncModbusTcpClient('192.168.1.50', port=502)
    await modbus_client.connect()
    
    if not modbus_client.connected:
        log.error("[!] CRITICAL ERROR: Failed to connect to Modbus Server.")
        return

    log.info("[+] Connected to Virtual PLC. Starting telemetry polling & publishing...")

    try:
        while True:
            response = await modbus_client.read_holding_registers(address=1, count=3, slave=1)
            
            if response.isError():
                log.error(f"[!] Modbus Read Error: {response}")
            else:
                registers = response.registers
                
                status_str = "RUNNING" if registers[0] == 1 else "STOPPED"
                payload = {
                    "device_id": "SIM-MOTOR-01",
                    "status": status_str,
                    "temperature_c": registers[1] / 10.0,
                    "vibration_mms": registers[2] / 100.0
                }
                
                # Publish JSON to MQTT Broker
                payload_json = json.dumps(payload)
                mqtt_client.publish(MQTT_TOPIC, payload_json)
                log.info(f"[MQTT PUB] {MQTT_TOPIC} -> {payload_json}")
            
            await asyncio.sleep(1.0)
            
    except asyncio.CancelledError:
        log.info("[*] Polling task cancelled by system.")
    except Exception as e:
        log.error(f"[!] Unexpected error during polling: {e}")
    finally:
        modbus_client.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        log.info("[*] Disconnected from Modbus and MQTT.")

if __name__ == "__main__":
    try:
        asyncio.run(poll_plc())
    except KeyboardInterrupt:
        log.info("[*] Gateway stopped by user.")