import sys
import time
import serial
import readchar


StartByte = 1  # SOH
PacketEnd = 4  # EOT
PacketACK = 6  # ACK
PacketNAK = 21 # NAK

ProtocolVersion = 65  # 'A'

BlinkCmd = 10
PanTiltCmd = 11

ser = None

def init_servo_control():
    global ser
    #ser = serial.Serial('/dev/ttyACM0',38400);
    ser = serial.Serial('/dev/tty.usbmodem1411',38400)  # Mac
    ser.flushInput()
    #ser.reset_input_buffer()  # >= v 3.0


def bytesToDec(b):
    return ','.join(map(lambda v: '%d:%s' % (ord(v),v),b))

def ser_write_str(s):
    global ser
    if sys.version_info.major < 3:
        ser.write(s)
    else:
        ser.write(bytes(s, 'ascii'))


def ser_write_bytes(l):
    global ser
    if sys.version_info.major < 3:
        ser.write(map(lambda c: chr(c),l))
    else:
        ser.write(bytes(l))


def ser_read_resp():
    global ser
    if sys.version_info.major < 3:
        ret = ser.read(size=2)
        return [int(ord(i)) for i in ret]
    else:
        return ser.read(size=2)


def sendBlinkCmd(count):
    global ser
    ser_write_bytes([StartByte, ProtocolVersion])
    ser_write_str("%d\n" % BlinkCmd)
    ser_write_str("%d\n" % count)
    ser_write_bytes([PacketEnd])
    ser.flush()
    ret = ser_read_resp()
    return len(ret) == 2 and ret[0] == PacketACK and ret[1] == BlinkCmd


def sendServoCmd(pan, tilt=None):
    global ser
    if tilt is None:
        tilt = pan
    ser_write_bytes([StartByte, ProtocolVersion])
    ser_write_str("%d\n" % PanTiltCmd)
    ser_write_str("%.2f\n" % pan)
    ser_write_str("%.2f\n" % tilt)
    ser_write_bytes([PacketEnd])
    ser.flush()
    ret = ser_read_resp()
    if len(ret) < 2:
        print('read timeout')
        ser.flushInput()
    elif ret[0] != PacketACK:
        print('error response: %s' % bytesToDec(ret))
    return len(ret) == 2 and ret[0] == PacketACK and ret[1] == PanTiltCmd


def set_pan_tilt(pan, tilt):
    return sendServoCmd(pan, tilt)


def sweep():
    global ser

    try:
        while True:
            print('10 .. 170')
            for a in range(10,171):
                sendServoCmd(a,a+5.0)
                time.sleep(5.0/1000.0)
            print('reverse')

            print('170 .. 10')
            for a in range(170,9,-1):
                sendServoCmd(a,a+5.0)
                time.sleep(20.0/1000.0)
            print('done')

            time.sleep(4)

    except Exception as e:
        print(e)
    finally:
        print('cleaning up')
        if ser.isOpen() and ser.inWaiting() > 0:  # ser.in_waiting()
            print(ser.readline())
        ser.close()


def arrow_control():
    global ser
    
    pan = 87.0
    tilt = 106.0
    sendServoCmd(pan, tilt)

    while True:
        prev_pan = pan
        prev_tilt = tilt

        c = readchar.readchar()
        if c == '\x03':
            break
        elif c == ' ': # space (return to home pos) 
            pan = 87.0
            tilt = 106.0
        elif c == '\x1b':  # ESC
            c = readchar.readchar()
            if c == '[':
                c = readchar.readchar()

                if c == 'A':  # up
                    tilt -= 5.0
                elif c == 'B': # down
                    tilt += 5.0
                elif c == 'C': # right
                    pan -= 5.0
                elif c == 'D': # left
                    pan += 5.0

        # Pan Servo (TowerPro)  range 10-180, center 87
        # Tilt Servo (HiTEC) range 20-180, center 100

        # keep in reasonable ranges
        if pan < 15:
            pan = 15.0
        elif pan > 170:
            pan = 170.0
        if tilt < 20:
            tilt = 20.0
        elif tilt > 170:
            tilt = 170.0

        if pan != prev_pan or tilt != prev_tilt:
            sendServoCmd(pan, tilt)
            print('Pan %.0f  Tilt %.0f' % (pan, tilt))
