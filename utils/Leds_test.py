import time
from utils.test_engine import TestEngine
from engine.hardware.arduino import WriteOnlyArduino

if __name__ == '__main__':
    engine = TestEngine()
    arduino = WriteOnlyArduino(engine)
    engine.run()

    if arduino.is_connected:
        engine.text('Arduino board connected')
        time.sleep(2.0)
        engine.text('starting all leds ...')
        arduino.hello_world()
    else:
        engine.text('No arduino board found ...')
        time.sleep(10.0)
        engine.text('Press escape key')
