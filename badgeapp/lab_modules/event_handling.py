################################################################################
# Section 1

# import time
# from demo_badge import Badge
# from demo_badge.expresslink import Event

# badge = Badge()
# badge.expresslink.connect()
# badge.expresslink.subscribe(1, "cloud/hello")

# while True:
#     badge.update()

#     event_id, parameter, mnemonic, detail = badge.expresslink.get_event()
#     if event_id == Event.STARTUP:
#         print("ExpressLink has started up. Ready to work!")
#     elif event_id == Event.MSG:
#         topic, message = badge.expresslink.get_message(parameter)
#         print(f"ExpressLink Event: received message on topic {topic}: {message}")

#     time.sleep(1) # only check once per second to reduce output

################################################################################
# Section 2

# from demo_badge import Badge
# from demo_badge.expresslink import Event

# badge = Badge()
# badge.expresslink.connect()
# badge.expresslink.subscribe(1, "cloud/hello")

# while True:
#     badge.update()

#     if badge.expresslink.event_signal.rose:
#         print("ExpressLink: events pending!")
#     elif badge.expresslink.event_signal.value:
#         print(badge.expresslink.get_event())

################################################################################
# Section 3

from demo_badge import Badge
from demo_badge.expresslink import Event

badge = Badge()

success, status, err = badge.expresslink.connect()
if not success:
    print(f"Unable to connect: {err} {status}")
    while True: pass

badge.expresslink.subscribe(1, "cloud/hello")

def handle_event():
    event_id, parameter, mnemonic, detail = badge.expresslink.get_event()
    if event_id == Event.STARTUP:
        print("ExpressLink has started up.\nReady to work!")
    elif event_id == Event.MSG:
        topic, message = badge.expresslink.get_message(parameter)
        print(f"Received message on topic {parameter} {topic}: {message}")
    elif event_id is None:
        print(f"No pending events.")

while True:
    badge.update()

    if badge.expresslink.event_signal.rose:
        print("ExpressLink: events pending!")
        badge.back_led.blink = 3
    elif badge.expresslink.event_signal.value:
        handle_event()

    if badge.button1.pressed:
        message = '{"message": "Hello from Demo Badge - to myself actually!"}'
        badge.expresslink.publish(1, message)
        print(f"Published a new message!")
