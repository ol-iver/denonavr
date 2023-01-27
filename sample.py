import asyncio
import denonavr
from denonavr.const import ZONE2

zones = {"Zone2": "Name of Zone2", "Zone3": "Name of Zone 3"}
d = denonavr.DenonAVR("192.168.1.171", add_zones=zones)


async def _update_callback(zone, event, parameter):

    print(d.zones[ZONE2].input_func)

    print(d.volume)


async def run_async():
    await d.async_setup()
    await d.async_telnet_connect()
    await d.async_update()

    d.register_callback("ALL", _update_callback)

    while True:
        await d.async_update()
        print(d.volume)
        await asyncio.sleep(5)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run_async())
loop.close()
