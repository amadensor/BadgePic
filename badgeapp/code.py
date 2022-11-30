from demo_badge import Badge, send_command, EXPRESSLINK_TX, EXPRESSLINK_RX
import busio
from demo_badge.expresslink import Event
import json

badge=Badge()
print('uart')
#uart = busio.UART(EXPRESSLINK_TX, EXPRESSLINK_RX, baudrate=115200, receiver_buffer_size=4096, timeout=0.1)

image="qr"
while True:

	badge.update()
	if badge.button1.pressed:
		image="qr"
	if badge.expresslink.event_signal.value:
		event_id, parameter, mnemonic, detail = badge.expresslink.get_event()
		if event_id == Event.MSG:
			topic, message = badge.expresslink.get_message(parameter)
			print(message)
			message_dict=json.loads(message)
			print(message_dict)
			image=message_dict['pic']
	"""if image=="qr":
		badge.show_qr_code("https://fp3rrylt2a.execute-api.us-east-2.amazonaws.com/")
	else:
		badge.show_picture(image)"""
	stat,ret=badge.expresslink.connected
	if stat:
		badge.show_picture(image)
	else:
		badge.show_picture('none')
		print('connect')
		badge.expresslink.connect()
		print('topic')
		badge.expresslink.subscribe(1,"badge/pic")

