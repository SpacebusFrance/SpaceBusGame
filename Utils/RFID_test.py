import serial
import time
import serial.tools.list_ports
from direct.showbase import DirectObject
import serial
from direct.showbase.ShowBase import ShowBase

START_CHAR = '<'
END_CHAR = '>'


def get_arduino_port():
    """

    Returns:

    """
    return [loc_port for loc_port in list(serial.tools.list_ports.comports())
            if 'Arduino' in loc_port.description or 'Arduino' in loc_port.manufacturer]


class Arduino(DirectObject.DirectObject):
    def __init__(self):
        super().__init__()
        arduino_ports = get_arduino_port()
        self._current_message = None
        arduino_ports = ['COM4']

        self.board = None
        if len(arduino_ports) == 1:
            print('Connecting to port', arduino_ports[0])
            self.board = serial.Serial(arduino_ports[0], 9600, timeout=5)
        else:
            print("No arduino connected !")
        time.sleep(0.1)
        self.add_task(self._event_polling, 'Hardware_Polling')

    def _event_polling(self, task):
        res = self.board.read().decode()
        if self._current_message is None and res == START_CHAR:
            print('Start reading ...')
            self._current_message = ""
        elif res == END_CHAR:
            print('Closing message, received', self._current_message)
            self._current_message = None
        elif self._current_message is not None and len(res) > 0:
            self._current_message += res
        return task.cont


class Test(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.arduino = Arduino()


if __name__ == '__main__':
    t = Test()
    t.run()


