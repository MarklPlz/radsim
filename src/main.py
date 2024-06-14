# Bibliotheken laden
import rp2
import network
import socket
import time
from machine import Pin
import uasyncio as asyncio
import ujson
import src.wifi_config as wc

SYS_DISTANCE = 0.131

zp1_sys1 = Pin(0, Pin.OUT)
zp1_sys2 = Pin(1, Pin.OUT)
zp2_sys1 = Pin(2, Pin.OUT)
zp2_sys2 = Pin(3, Pin.OUT)
zp3_sys1 = Pin(4, Pin.OUT)
zp3_sys2 = Pin(5, Pin.OUT)
zp4_sys1 = Pin(6, Pin.OUT)
zp4_sys2 = Pin(7, Pin.OUT)
life_signal = Pin(8, Pin.OUT)
onboard_led = Pin("LED", Pin.OUT, value=0)
input_pin1 = Pin(10, Pin.IN)
input_pin2 = Pin(11, Pin.IN)
input_pin3 = Pin(12, Pin.IN)
input_pin4 = Pin(13, Pin.IN)
input_pin5 = Pin(14, Pin.IN)
input_pin6 = Pin(15, Pin.IN)
input_pin7 = Pin(16, Pin.IN)
input_pin8 = Pin(17, Pin.IN)
input_pin9 = Pin(18, Pin.IN)
input_pin10 = Pin(19, Pin.IN)


def setup_access_point():
    # Create Access Point
    rp2.country('AT')
    ap = network.WLAN(network.AP_IF)

    ap.active(False)
    time.sleep(0.1)

    ap.config(essid=wc.SSID, password=wc.KEY, security=4, channel=6)

    ap.active(True)
    time.sleep(0.1)

    ap.ifconfig((wc.IP,wc.SUBNET,wc.GATEWAY,wc.DNS))

    # Print AP Config
    print('Access point active')
    print('SSID:', ap.config('essid'))
    print('IP address:', ap.ifconfig()[0])
    return ap
 
 
def get_html():
    html_url = "../public/index.html"
    css_url = "../public/css/style.css"
    page = open(html_url, "r")
    html = page.read()
    page.close()
    page = open(css_url, "r")
    css = page.read()
    page.close()

    html = html.replace('<link rel="stylesheet" type="text/css" href="css/style.css">', '<style>'+css+'</style>')
    return html


async def serve_client(reader, writer, countinghead_timestamps):
    response = get_html()
    response = response.replace('IP', wc.IP)
    
    request_line = await reader.readline()
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    led_on = request.find('/light/on')
    led_off = request.find('/light/off')

    if led_on == 6:
        response = response.replace('/*animation*/',
                                    'animation: moveTrain '
                                    +str(countinghead_timestamps[-1][-1])
                                    +'s linear 1 forwards;')
        response = response.replace('/* Ende */\n    0%', 
                                    '/* Ende */\n    100%')
        trigger_countingheads(countinghead_timestamps)

    if led_off == 6:
        response = response.replace('/*animation*/',
                                    'animation: moveTrain '
                                    +str(countinghead_timestamps[-1][-1])
                                    +'s linear 1 forwards;')
        response = response.replace('/* Anfang */\n    0%',
                                    '/* Anfang */\n    100%')
        trigger_countingheads(countinghead_timestamps)

    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()


def load_train():
    with open("../config/train.json", "r") as file:
        try:
            train = ujson.load(file)
        except ValueError as exception:
            print(exception)
    return train


def get_wheel_timestamps():
    train = load_train()
    no_wheels = train["no_bogie_wheels"] * 2 * train["no_carriages"]
    carriage_spacing = (train["train_length"]-train["no_carriages"]
                        *train["trunnion_spacing"])/train["no_carriages"]
    speed = (train["speed"]/3.6)
    
    # schleife einfügen statt hardcoden
    wheel_timestamps = [0] * no_wheels
    wheel_timestamps[0] = carriage_spacing/2/speed
    wheel_timestamps[1] = wheel_timestamps[0]+train["bogie_axle_spacing"]/speed
    wheel_timestamps[2] = wheel_timestamps[0]+train["trunnion_spacing"]/speed
    wheel_timestamps[3] = wheel_timestamps[1]+train["trunnion_spacing"]/speed
    wheel_timestamps[4] = wheel_timestamps[3]+carriage_spacing/speed
    wheel_timestamps[5] = wheel_timestamps[4]+train["bogie_axle_spacing"]/speed
    wheel_timestamps[6] = wheel_timestamps[4]+train["trunnion_spacing"]/speed
    wheel_timestamps[7] = wheel_timestamps[5]+train["trunnion_spacing"]/speed
    wheel_timestamps[8] = wheel_timestamps[7]+carriage_spacing/speed
    wheel_timestamps[9] = wheel_timestamps[8]+train["bogie_axle_spacing"]/speed
    wheel_timestamps[10] = wheel_timestamps[8]+train["trunnion_spacing"]/speed
    wheel_timestamps[11] = wheel_timestamps[9]+train["trunnion_spacing"]/speed
    return wheel_timestamps


def get_countinghead_timestamps(wheel_timestamps):
    countinghead_timestamps = [[0] * len(wheel_timestamps) for _ in range(4)]
    for i in range(len(countinghead_timestamps)):
        for j in range(len(countinghead_timestamps[0])):
            countinghead_timestamps[i][j] = wheel_timestamps[j]+i*(
                                                wheel_timestamps[-1]+1)
    return countinghead_timestamps


def trigger_countingheads(countinghead_timestamps):
    start_time = time.time()
    for i in range(len(countinghead_timestamps)):
        for j in range(len(countinghead_timestamps[0])):
            if time.time() >= start_time+countinghead_timestamps[i][j]:
                set_countingheadpin(i)


def set_countingheadpin(countinghead):
    train = load_train()
    time_sys = SYS_DISTANCE/(train["speed"]/3.6)
    if countinghead == 0:
        zp1_sys1.value(1)
        time.sleep(time_sys)
        zp1_sys2.value(1)
        time.sleep(time_sys)
        zp1_sys1.value(0)
        time.sleep(time_sys)
        zp1_sys2.value(0)
    elif countinghead == 1:
        zp2_sys1.value(1)
        time.sleep(time_sys)
        zp2_sys2.value(1)
        time.sleep(time_sys)
        zp2_sys1.value(0)
        time.sleep(time_sys)
        zp2_sys2.value(0)
    elif countinghead == 2:
        zp3_sys1.value(1)
        time.sleep(time_sys)
        zp3_sys2.value(1)
        time.sleep(time_sys)
        zp3_sys1.value(0)
        time.sleep(time_sys)
        zp3_sys2.value(0)
    elif countinghead == 3:
        zp4_sys1.value(1)
        time.sleep(time_sys)
        zp4_sys2.value(1)
        time.sleep(time_sys)
        zp4_sys1.value(0)
        time.sleep(time_sys)
        zp4_sys2.value(0)
    else:
        print('Error setting pin')
        print(countinghead)
        
        
        
async def main():
    wheel_timestamps = get_wheel_timestamps()
    countinghead_timestamps = get_countinghead_timestamps(wheel_timestamps)
    ap = setup_access_point()
    wrapper_func = lambda reader, writer: serve_client(reader, writer, 
                                                       countinghead_timestamps)
    asyncio.create_task(asyncio.start_server(wrapper_func, "0.0.0.0", 80))
    print('\nWebserver active')
    print('http://', ap.ifconfig()[0], sep='')
    while True:
        onboard_led.on()
        life_signal.value(1)
        await asyncio.sleep(2)
        onboard_led.off()
        life_signal.value(0)
        await asyncio.sleep(4)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
    
if __name__ == "__main__":
    main()
