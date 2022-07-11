import serial
import time
import serial.tools.list_ports


class Arduino:
    def __init__(self):
        ports = list(serial.tools.list_ports.comports())
        self.board = None
        self.num_leds = 60
        ports = list(serial.tools.list_ports.comports())
        self.board = None
        for p in ports:
            print(p, p.description)
            # if "Arduino" in p[1]:
            if p.description != "n/a":
                self.board = serial.Serial(p[0], 9600, timeout=5)
        if self.board is None:
            print("No _arduino connected !")
        time.sleep(0.1)

    def all_off(self):
        self.board.write(str.encode("off"))

    def all_on(self):
        self.board.write(str.encode("on"))

    def led(self, num, on):
        print("lightning led :", num, "to :", on)
        if isinstance(num, list):
            for e in num:
                self.board.write(str.encode(str(e) + "-" + str(on)))
        else:
            self.board.write(str.encode(str(num) + "-" + str(on)))

    def test_all_leds(self):
        for i in range(self.num_leds):
            print("Switch led :\033[96m", i, "\033[0m : \033[95mON\033[0m")
            self.board.write(str.encode(str(i) + "-1"))
            time.sleep(0.5)
            self.board.write(str.encode(str(i) + "-0"))


if __name__ == '__main__':
    h = Arduino()

    print("===========\nTesting all leds\n===========\n")

    # h.all_off()
    #
    # h.led(2, 0)
    #
    # h.all_on()
    h.test_all_leds()
