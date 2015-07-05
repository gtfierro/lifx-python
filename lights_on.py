from lifx import *
import time

lifx.get_lights()

# Turn on all lights at once wih a broadcast
#lifx.set_power(lifx.ALL, True)

# Turn on all lights in the network, one at a time
for light in lifx.lights:
    lifx.set_power(lifx.lights[light].addr, True)
    time.sleep(1)