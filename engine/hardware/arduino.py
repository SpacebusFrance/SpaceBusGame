import time

from serial import Serial
from serial.tools import list_ports

from engine.utils.logger import Logger


class WriteOnlyArduino:
    """
    A class representing the read-only _arduino used to manage leds.
    """
    def __init__(self, engine):
        self.task_mgr = engine.task_mgr

        ports = list(list_ports.comports())
        self.board = None
        for p in ports:
            # Logger.info(p, p[2], 'description :', p.description)
            if "ttyACM0" in p.description:
                self.board = Serial(p[0], 9600, timeout=5)

        if self.board is None:
            Logger.warning("no arduino board connected !")
        else:
            if self.board.isOpen():
                Logger.info("port is open. Closing it")
                self.board.close()

            Logger.info("opening the port for arduino connection")
            self.board.open()

        time.sleep(1.0)
        self.all_off()

    @property
    def is_connected(self) -> bool:
        return self.board is not None and self.board.isOpen()

    def __exit__(self, **kwargs):
        if self.board.isOpen():
            self.board.close()

    def hello_world(self):
        """
        All led sets one after one and switch them off
        """
        self.all_off()
        for i in range(50):
            self.led_on(i)
            time.sleep(.1)
        time.sleep(1.0)
        self.all_off()

    def send(self, s):
        """
        Sends a message to the _arduino
        @param s: te message
        """
        if self.board is not None:
            self.board.write(str.encode(str(s.strip())))

    def led_on(self, id):
        """
        Switches led(s) on
        @param id: the id(s) of the desired led(s). Can be an int or a list of int.
        """
        if isinstance(id, list):
            for i in id:
                self.send(f"<{i}'-1>")
        else:
            self.send(f"<{id}-1>")

    def led_off(self, id):
        """
        Switches led(s) off
        @param id: the id(s) of the desired led(s). Can be an int or a list of int.
        """
        if isinstance(id, list):
            for i in id:
                self.send(f"<{i}-0>")
        else:
            self.send(f"<{id}-0>")

    def all_on(self):
        """
        Switches all leds on
        """
        self.send("<on>")

    def all_off(self):
        """
        Switches all leds off
        """
        self.send("<off>")
