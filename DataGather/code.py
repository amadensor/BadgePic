import time
import json
import uuid
from demo_badge import Badge

badge=Badge()
badge.expresslink.config.QoS=1
badge.expresslink.config.set_topic(1,'badge/rawdata')
prev_time=0
data_queue=[]

def send_data():
    (con1,con2)=badge.expresslink.connected
    if con1:
        badge.expresslink.config.QoS=1
        badge.expresslink.config.set_topic(1,'badge/rawdata')
        data=data_queue.pop()
        badge.expresslink.publish(1,json.dumps(data))
    else:
        badge.expresslink.connect()

while True:
    badge.update()
    num_items=len(data_queue)
    for t in range(5):
        if num_items>t:
            badge.leds[t]=(0,100,0)
        else:
            badge.leds[t]=(0,0,0)
    if time.monotonic() > prev_time+30:
        data={
        "id":str(uuid.uuid4()),
        "ts":time.monotonic(),
        "Celcius":badge.temperature_humidity.temperature,
        "Humidity":badge.temperature_humidity.relative_humidity,
        "Light":badge.ambient_light.value
        }
        data_queue.append(data)
        prev_time=time.monotonic()
    if len(data_queue)>0:
        send_data()

