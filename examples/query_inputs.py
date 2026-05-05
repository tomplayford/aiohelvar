#!/usr/bin/env python3

"""Queries all devices for their inputs, 
    and starts polling the devices that had inputs,
    then prints input state changes to the console.

WARNING: Polling happens every second for every device 
    so it may slow down the router or do other unwanted things
    if ran on a large installation!
"""

import asyncio
from datetime import datetime
from aiohelvar.router import Router
import logging

from aiohelvar.parser.parser import CommandParser

import aiohelvar.exceptions
try:
    from rich import print
except ImportError:
    pass
POLL_INTERVAL = 2.0
async def main():
    parser = CommandParser()
    router_ip_address = "10.254.1.1"
    router_helvarnet_port = 50000

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)

    print(f"Connecting to router at address: {router_ip_address}...")
    router = Router(router_ip_address, router_helvarnet_port)
    await router.connect()
    print(f"Connected to router on workgroup: {router.workgroup_name}. Initializing router...")
    await router.initialize()
    print("Initialized router. Devices detected: ", len(router.devices.devices))
    await asyncio.sleep(2)
    
    devices_with_type = [d for d in router.devices.devices.values() if d.type]

    print(f"\nQuerying inputs ({len(devices_with_type)} devices with any device type):")
    device_state = {}
    for addr, device in router.devices.devices.items():
        if not device.type:
            continue
        print(f" - {device.name} ( type: {device.type} )")
        
        
        try:
            response = await router.devices.query_inputs(device)
            if response:
                print(f"     - {response}")
                device_state[device] = response
            else:
                print("     - (no response???)")
        except aiohelvar.exceptions.PropertyDoesNotExistError:
            print("     - N/A")

    print(f"Found {len(device_state)} devices with queryable inputs. Starting polling...")
    printed_dots = False
    loop = asyncio.get_running_loop()
    while True:
        device_state_loop = list(device_state.items())
        count = len(device_state_loop)

        if count == 0:
            print("No devices with queryable inputs.")
            return

        # Spread the queries evenly across one second
        interval = POLL_INTERVAL / count
        start_time = loop.time()

        for i, (device, state) in enumerate(device_state_loop):

            try:
                new_state = await router.devices.query_inputs(device)
                if new_state != state:
                    if printed_dots:
                        printed_dots = False
                        print()
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Inputs changed for {device.name}: {new_state} (old {state})")
                    device_state[device] = new_state
            except aiohelvar.exceptions.PropertyDoesNotExistError:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Device {device.name} no longer has queryable inputs??")
                # remove from the live state dict if it's still present
                device_state.pop(device, None)

            # Calculate when the next task should start and adapt sleep
            next_start = start_time + ((i + 1) * interval)
            now = loop.time()
            delay = next_start - now
            if delay > 0:
                await asyncio.sleep(delay)

        printed_dots = True
        print(".", end="", flush=True)


asyncio.run(main())
