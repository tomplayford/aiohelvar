#!/usr/bin/env python3

"""Queries all devices for their inputs, 
    and starts polling the devices that had inputs,
    then prints input state changes to the console.

WARNING: Polling happens every second for every device 
    so it may slow down the router or do other unwanted things
    if ran on a large installation!
"""

import asyncio
from aiohelvar.router import Router
import logging

from aiohelvar.parser.parser import CommandParser

import aiohelvar.exceptions

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
                print("     - ",response)
                device_state[device] = response
            else:
                print("     - ","(no response???)")
        except aiohelvar.exceptions.PropertyDoesNotExistError:
            print("     - ","N/A")

    print(f"Found {len(device_state)} devices with queryable inputs. Starting polling...")
    printed_dots = False
    while True:
        # print changes in state boolean field list
        for device, state in device_state.items():
            try:
                new_state = await router.devices.query_inputs(device)
                if new_state != state:
                    if printed_dots:
                        printed_dots=False
                        print()
                    print(f"Device {device.name} state changed: {state} -> {new_state}")
                    device_state[device] = new_state
            except aiohelvar.exceptions.PropertyDoesNotExistError:
                print(f"Device {device.name} no longer has queryable inputs??")
                del device_state[device]
            await asyncio.sleep(0)
        await asyncio.sleep(1)
        printed_dots  = True
        print(".", end="", flush=True)


asyncio.run(main())
