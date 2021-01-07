import logging
_log = logging.getLogger(__name__)

import settings
import uasyncio as asyncio

from ds18x20 import DS18X20
from homie.node import HomieNode
from homie.device import HomieDevice, await_ready_state
from homie.property import HomieProperty
from homie.constants import FLOAT

from machine import Pin
from onewire import OneWire


class DS18B20(HomieNode):
    def __init__(self, name="One Wire DS18B20", pin=12, interval=10, pull=-1):
        super().__init__(id="ds18b20", name=name, type="ds18b20")
        self.ds18b20 = DS18X20(OneWire(Pin(pin)))
        addrs = self.ds18b20.scan()
        if not addrs:
            raise Exception("no DS18B20 found at bus on pin %d" % pin)
        # save what should be the only address found
        self.addr = addrs.pop()
        self.interval = interval

        self.p_temp = HomieProperty(
            id="temperature",
            name="Temperature",
            datatype=FLOAT,
            format="-40:80",
            unit="°F",
            default=0,
        )
        self.add_property(self.p_temp)

        asyncio.create_task(self.update_data())

    @await_ready_state
    async def update_data(self):
        delay = self.interval * 1000

        while True:
            self.p_temp.value = await self.read_temp()
            await asyncio.sleep_ms(delay)

    async def read_temp(self, fahrenheit=True):
        """
        Reads temperature from a single DS18X20
        :param fahrenheit: Whether or not to return value in Fahrenheit
        :type fahrenheit: bool
        :return: Temperature
        :rtype: float
        """
        self.ds18b20.convert_temp()
        await asyncio.sleep_ms(750)
        temp = self.ds18b20.read_temp(self.addr)
        if fahrenheit:
            ntemp = temp
            self.device.dprint("Temp: " + str(self.c_to_f(ntemp)))
            return self.c_to_f(ntemp)
        return temp

    @staticmethod
    def c_to_f(c):
        """
        Converts Celsius to Fahrenheit
        :param c: Temperature in Celsius
        :type c: float
        :return: Temperature in Fahrenheit
        :rtype: float
        """
        return (c * 1.8) + 32


def main():
    homie = HomieDevice(settings)
    homie.add_node(DS18B20())
    homie.run_forever()


if __name__ == "__main__":
    main()
