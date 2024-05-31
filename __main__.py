# Bibliotheken laden
import rp2
import network
import socket
import time
from machine import Pin
import uasyncio as asyncio

led = Pin(15, Pin.OUT)
onboard = Pin("LED", Pin.OUT, value=0)

ssid = 'RadsimWIFI'
pw = 'picorsr123'
IP =      '192.168.4.1'
SUBNET =  '255.255.255.0'
GATEWAY = '192.168.4.1'
DNS =     '0.0.0.0'

def setup_access_point():
    # WAP-Betrieb
    rp2.country('AT')
    ap = network.WLAN(network.AP_IF)

    ap.active(False)
    time.sleep(0.1)

    # WAP-Konfiguration
    ap.config(essid=ssid, password=pw, security=4, channel=6)

    # WLAN-Interface aktivieren
    ap.active(True)
    time.sleep(0.1)

    ap.ifconfig((IP,SUBNET,GATEWAY,DNS))

    # Ausgabe der Netzwerk-Konfiguration
    print('Access Point Active')
    print('SSID:', ap.config('essid'))
    print('IP Address:', ap.ifconfig()[0])
    
def getHTML():
    url = "./index.html"
    page = open(url, "r")
    html = page.read()
    page.close()
    return html

async def serve_client(reader, writer):
    response = getHTML()
    response = response.replace('IP', IP)
    
    request_line = await reader.readline()
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    led_on = request.find('/light/on')
    led_off = request.find('/light/off')

    if led_on == 6:
        onboard.on()
        response = response.replace('/*animation*/',
                                    'animation: moveTrain 5s linear 1 forwards;')
        response = response.replace('100% {  /* Anfang */', '0% {  /* Anfang */')
        response = response.replace('0% {  /* Ende */', '100% {  /* Ende */')

    if led_off == 6:
        onboard.off()
        response = response.replace('/*animation*/',
                                    'animation: moveTrain 5s linear 1 forwards;')
        response = response.replace('0% {  /* Anfang */', '100% {  /* Anfang */')
        response = response.replace('100% {  /* Ende */', '0% {  /* Ende */')

    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()

async def main():
    print('Setting up Access Point...')
    setup_access_point()

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        print("heartbeat")
        await asyncio.sleep(5)
        
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
    
if __name__ == "__main__":
    main()