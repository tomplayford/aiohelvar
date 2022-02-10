# aiohelvar
Asynchronous Python library to interact with Helvar Routers.

This library was originally written to support the (work in progress) Helvar Home Assistant integration. 

Features:
* Manages the async TCP comms well, keeps the connection alive and listens to broadcast messages
* Decodes the HelvarNet messages and translates things into Python objects that can easily be further translated into Home Assistant objects
* Discovers and retrieves Devices, Groups & Scenes and and all their properties, state and values.
* Keeps track of device states as scenes and devices change based on notifications from the router.
* Calls the more useful commands to control or read status from the above.

Very much a work in progress. Known TODOS:

* Cluster support - we assume cluster 0 at the moment
* Sensor support
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
If you're having trouble here, I suggest we implement a device polling option that can be enabled. 

### Colour changing loads.

I don't have a router that supports these as native DALI devices. So I have no idea how they appear :)

The HelvarNET docs don't mention how it's supported. 


## Requests to Helvar :)

* Please provide a command to retrieve a device's GTIN and serial number.

## Disclaimer

Halvar (TM) is a registered trademark of Helvar Ltd.

This software is not officially endorsed by Helvar Ltd in any way.

The authors of this software provide no support, guarantees, or warranty for its use, features, safety, or suitability for any task. We do not recommend you use it for anything at all, and we don't accept any liability for any damages that may result from its use.

This software is licensed under the Apache License 2.0. See the LICENCE file for more details. 


