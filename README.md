# aiohelvar
Asynchronous Python library to interact with Helvar Routers.

This library written to support the (work in progress) [Helvar HomeAssistant integration](https://github.com/tomplayford/homeassistant_helvar/). 

Features:
* Manages the async TCP comms well, keeps the connection alive and listens to broadcast messages
* Decodes the HelvarNet messages and translates things into Python objects that can easily be further translated into Home Assistant objects
* Discovers and retrieves Devices, Groups & Scenes and and all their properties, state and values.
* Keeps track of device states as scenes and devices change based on notifications from the router.
* Calls the more useful commands to control or read status from the above.

Very much a work in progress. Known TODOS:

* Cluster support - we assume cluster 0 at the moment
* Sensor support
* Support relative changes to scene levels update commands
* Better test coverage

## (Some of the) Known limitations 

### Lack of unique device IDs

I can't find a way to grab a unique ID for devices on the various Router busses. 

The DALI standard requires every device have a GTIN and a unique serial number. These appear in Helvar's router management software, but are not available on the 3rd party APIs. I've tried probing for undocumented commands with no luck. 

For now, I'm using the workgroup name + the helvar bus address as a unique address. This is *not* unique per physical device - it is, however, unique at any point in time. 

Open to better suggestions!

### Routers don't notify changes to individual devices.

We receive notifications when group scenes change, and since we know device levels for every scene, we can update devices levels without polling devices. 

However, we don't get notified when individual devices change their load. This shouldn't be an issue for most setups, as Helvar is scene oriented, and almost every happens that way. 

We also receive notifications when there are relative changes to scene levels, but we don't currently support those commands. 

If you're having trouble here, I suggest we implement a device polling option that can be enabled. 

### Router doesn't report decimal scene levels

If you set scene levels to a decimal, rather than an int. (e.g. 0.2 or 54.6). The only command available to retrieve scene levels only
returns the integer. 

The only time this is really a problem on dim scenes where a value of 0.25 would show light, but the command is reporting off. 

We get round this by polling all devices manually if we think they've been updated by a scene. Don't like it. 

### Colour changing loads.

I don't have a router that supports these as native DALI devices. So I have no idea how they appear :)

The HelvarNET docs don't mention how it's supported. 


## Requests to Helvar :)

* Please provide a command to retrieve a device's GTIN and / or serial number.
* Please provide a command to retrieve full decimal values of a scene table.

## Disclaimer

Halvar (TM) is a registered trademark of Helvar Ltd.

This software is not officially endorsed by Helvar Ltd in any way.

The authors of this software provide no support, guarantees, or warranty for its use, features, safety, or suitability for any task. We do not recommend you use it for anything at all, and we don't accept any liability for any damages that may result from its use.

This software is licensed under the Apache License 2.0. See the LICENCE file for more details. 

## Development

### Installing Test Dependencies

To run tests, you need to install the test dependencies:

```bash
pip install -r requirements-test.txt
```

### Running Tests

Run all tests:

```bash
python3 -m pytest
```


