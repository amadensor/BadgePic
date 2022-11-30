import os
import binascii
import aesio
import displayio
import struct
import microcontroller

from demo_badge import Badge
from demo_badge.expresslink import Event, OTACodes

#### CHANGE ME ####### without https:// or trailing slash ######################
CompanionWebAppURL  = 'EXAMPLE.cloudfront.net'
################################################################################

# Start badge
badge = Badge()

def init_display_resources(x, y, depth):
    # Instantiate tile grid and allocate large buffer
    bitmap = displayio.Bitmap(x, y, depth)
    group = displayio.Group(scale=1)
    tileGrid = displayio.TileGrid(
        bitmap,
        pixel_shader=displayio.ColorConverter(
            input_colorspace=displayio.Colorspace.RGB565
        )
    )
    group.append(tileGrid)
    return group, bitmap

# Allocate a large buffer of 240x240 pixels with 16-bit colors
group, bitmap = init_display_resources(240, 240, 2**16)

def init_companion_url(badge):
    # Get AES parameters from non-volatile storage or initialize them
    if microcontroller.nvm[:3] == b'AES':
        # Each value is 16 bytes long
        random_key = microcontroller.nvm[3:3+16]
        random_iv  = microcontroller.nvm[3+16:3+16+16]
        print("Loaded existing AES encryption key and initialization vector from non-volatile storage.")
    else:
        # Generate random a 128-bit AES key and IV = 16 bytes each
        # Note: make sure the source of randomness is suitable for cryptography and secure number generators!
        random_key = os.urandom(int(128/8))
        random_iv = os.urandom(int(128/8))

        # Store AES parameters in non-volatile storage
        # Each assignment causes an erase and write cycle so its recommended to assign all values at once.
        microcontroller.nvm[0:3+16+16+1] = b'AES' + random_key + random_iv + b'\x00'
        print("Stored new AES encryption key and initialization vector in non-volatile storage.")

    # Get easy-to-use ASCII version
    random_key = binascii.hexlify(random_key).decode('ascii')
    random_iv = binascii.hexlify(random_iv).decode('ascii')

    # Remove "-" from thingName UUID, concatenate with key and iv
    thing_name = badge.expresslink.config.ThingName
    qr_payload = thing_name.replace("-", "") + random_key + random_iv

    # Encode as base64 and remove the new line
    qr_payload_b64 = binascii.b2a_base64(binascii.unhexlify(qr_payload)).strip().decode()

    # Replace =, + and \ with url safe characters
    qr_payload_b64_str = qr_payload_b64.replace("+", ".").replace("/", "_")

    # Build final URL
    qr_payload_out = f"https://{CompanionWebAppURL}/picture_transfer.html?{qr_payload_b64_str}"

    # Display the URL on the serial console
    print("\n"*3)
    print(f"Thing Name: {thing_name}")
    print(f"AES key: {random_key}")
    print(f"AES IV: {random_iv}")
    print()
    print("Open this website on your laptop in a new browser tab. Or use your phone to scan the QR code.")
    print(qr_payload_out)
    print("\n"*3)

    # Render a QR code on the display
    badge.show_qr_code(qr_payload_out)

    return random_key, random_iv

# Generate QR code and display it
random_key, random_iv = init_companion_url(badge)

def process_event_OTA(parameter, mnemonic, detail):
    if parameter == OTACodes.HostUpdateProposed:
        print("EVENT: OTA Proposal received.")
        code, _ = badge.expresslink.ota_state
        if code == OTACodes.HostUpdateProposed:
            print("New OTA available and ready to be accept.")
            badge.expresslink.ota_accept()
            print("OTA job accepted. ExpressLink is downloading the encrypted payload (takes up to 1 min)...")
    elif parameter == OTACodes.NewHostImageReady:
        print("EVENT: OTA payload download completed. Decrypting now...")
        fetch_picture()
    else:
        print(f"Ignoring unhandled OTA event: {parameter} {mnemonic} {detail}.")

def fetch_picture():
    # Prepare the screen
    badge.display.show(group)

    # Initialize scratch variables and some constants
    INTERLACE_LEVEL = 1
    BLOCK_SIZE = 480
    render_position = 0
    read_position = 0
    iv = random_iv

    badge.expresslink.debug = False
    print("Going silent on ExpressLink command output... watch the display for your picture!")

    # For each pixel row on the display
    for y in range(0, 240, INTERLACE_LEVEL):
        # Fetch data from OTA blob and advance reading position
        badge.expresslink.ota_seek(read_position)
        # Add BLOCK_SIZE to counter; move to the next row
        read_position += BLOCK_SIZE * INTERLACE_LEVEL
        # Read BLOCK_SIZE from OTA payload
        _, ota_msg, _ = badge.expresslink.ota_read(BLOCK_SIZE)
        ota_bytes = bytearray(binascii.unhexlify(ota_msg[4:4+BLOCK_SIZE*2]))
        # Decrypt data
        ota_bytes, iv = decrypt_row(ota_bytes, BLOCK_SIZE, random_key, iv)
        # Render a full row of pixels
        render_position = render_row(y, ota_bytes, BLOCK_SIZE, render_position)
        print(f"Decrypting and rendering pixel row {y+1} out of 240.")

    badge.expresslink.debug = True

    # Complete the OTA job
    badge.expresslink.ota_close()
    print("Enjoy your picture - it's fully rendered on the display!")

def decrypt_row(ota_bytes, block_size, key, iv):
    inp = bytearray(16)
    outp = bytearray(16)
    key = binascii.unhexlify(key)
    if isinstance(iv, str): # previous iteration might have already converted it to binary
        iv = binascii.unhexlify(iv)

    # Split message into 16 byte chunks = 30 chunks
    for x in range(block_size/16):
        # Copy data to decrypt into inp buffer
        inp = ota_bytes[x*16:x*16+16]
        # Configure cipher using key and new IV
        cipher = aesio.AES(key, aesio.MODE_CBC, iv)
        # Decrypt 16 bytes and store them in outp buffer
        cipher.decrypt_into(inp, outp)
        # Use previous ciphertext as new IV
        iv = bytes(inp)
        # Copy outp buffer into original buffer
        for j in range(16):
            ota_bytes[x*16+j] = outp[j]
    return ota_bytes, iv

def render_row(y, ota_bytes, block_size, i):
    for x in range(240):
        # Take two bytes and combine them to produce a 16-bit integer using big-endian (>) unsigned short (H)
        bitmap[x, y] = struct.unpack('>H', bytes([ota_bytes[i], ota_bytes[i+1]]))[0]
        i += 2
        if i == block_size:
            i = 0 # reset once it gets to BLOCK_SIZE
    return i

# Connect to AWS, stop if there is any error
success, status, err = badge.expresslink.connect()
if not success:
    print(f"Unable to connect: {err} {status}")
    while True: pass

while True:
    badge.update()

    if badge.expresslink.event_signal.value:
        event_id, parameter, mnemonic, detail = badge.expresslink.get_event()
        if not event_id:
            pass # no event pending
        elif event_id == Event.OTA:
            process_event_OTA(parameter, mnemonic, detail)
        else:
            print(f"Ignoring unhandled event: {event_id} {parameter} {mnemonic} {detail}")
