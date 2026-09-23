from gpiozero import LED
from time import sleep

# GPIO pins
ir_pin = 17       # IR LED stays on
white_pin = 27    # White LED flashes

# Initialize LEDs
ir_led = LED(ir_pin)
white_led = LED(white_pin)

# Turn on IR LED indefinitely
ir_led.on()

try:
    while True:
        # Flash white LED
        white_led.on()
        sleep(0.2)    # LED stays on for 0.2 seconds
        white_led.off()
        sleep(4.8)    # Wait 4.8 seconds before next flash
except KeyboardInterrupt:
    # Turn off everything on exit
    ir_led.off()
    white_led.off()
    print("Exiting safely")
