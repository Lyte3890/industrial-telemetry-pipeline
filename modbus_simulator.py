import asyncio
import math
import random
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
log = logging.getLogger("Simulator")
logging.getLogger("pymodbus").setLevel(logging.ERROR)

async def update_sensor_data(context):
    log.info("[*] Starting async sensor telemetry simulation...")
    
    register_address = 0x01
    slave_id = 0x01
    tick = 0
    
    await asyncio.sleep(1)
    
    while True:
        temp_c = 40.0 + 5.0 * math.sin(tick * 0.1) + random.uniform(-0.5, 0.5)
        vib_mms = 1.0 + 0.5 * math.sin(tick * 0.5) + random.uniform(-0.1, 0.1)
        
        if random.random() < 0.05:
            vib_mms += random.uniform(2.0, 6.0)
            log.warning(f"[!] Simulated Anomaly Spike! Vibration: {vib_mms:.2f} mm/s")
            
        values = [1, int(temp_c * 10), int(max(0, vib_mms * 100))]
        
        # Thread-safe write to context for pymodbus 3.5.x
        context[slave_id].setValues(3, register_address, values)
        
        tick += 1
        await asyncio.sleep(1.0)

async def run_simulator():
    store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(1, [0] * 100))
    context = ModbusServerContext(slaves={1: store}, single=False)
    
    task = asyncio.create_task(update_sensor_data(context))
    
    log.info("[*] Starting Modbus TCP Server on 127.0.0.1:5020...")
    await StartAsyncTcpServer(context=context, address=("127.0.0.1", 5020))
    task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(run_simulator())
    except KeyboardInterrupt:
        log.info("[*] Server stopped by user.")