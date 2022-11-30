import json
from demo_badge import Badge
from adafruit_ticks import ticks_add, ticks_less, ticks_ms

################################################################################

badge = Badge()

success, status, err = badge.expresslink.connect()
if not success:
    print(f"Unable to connect: {err} {status}")
    while True: pass

update_rate = 2000 # milliseconds
next_data_update = ticks_ms()

badge.expresslink.config.set_topic(1, "$aws/rules/demo_badge_sensors")

################################################################################

print("Looping...")
while True:
    badge.update()

    if ticks_less(next_data_update, ticks_ms()):
        # read data from sensors and build JSON message
        msg = json.dumps({
            "temperature": badge.temperature_humidity.temperature,
            "humidity": badge.temperature_humidity.relative_humidity,
            "light": float(badge.ambient_light.value),
        })

        # publish message in JSON format to MQTT
        print("Sending fresh sensor data...")
        badge.expresslink.publish(1, msg)

        # set the next data update timestamp
        next_data_update = ticks_add(ticks_ms(), update_rate)
