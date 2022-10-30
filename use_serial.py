import serial
import time

from to_inference import Inference

class Interactive_serial(object):
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.port = "/dev/ttyUSB0"
        self.ser.baudrate = 921600
        self.ser.bytesize = 8
        self.ser.parity = 'N'
        self.ser.stopbits = 1
        try:
            self.ser.open()
        except:
            self.ser.close()
            print("Serial Open Error")
    # 串口掉线重连
    def serial_connection(self):
        self.ser.port = "/dev/ttyUSB0"
        self.ser.baudrate = 921600
        self.ser.bytesize = 8
        self.ser.parity = 'N'
        self.ser.stopbits = 1
        try:
            self.ser.open()
            print('Reconnection Success')
        except:
            self.ser.close()
            print("Serial Reconnection Error")
    # 串口发送移动信息
    def send_data(self):
        while True:
            time.sleep(0.0005)
            try:
                if Inference.DEVIATION_X == 0:
                    self.ser.write(('S' + str(2) + str(0) + str(0) + str(0) + str(0) + 'E').encode("utf-8"))
                    
                elif   Inference.LOW_EIGHT / 100 >= 1:
                    self.ser.write(('S' + str(Inference.DIRECTION) + str(Inference.HIGH_EIGHT) + str(Inference.LOW_EIGHT) + 'E').encode("utf-8"))

                elif Inference.LOW_EIGHT / 10 >= 1:
                    self.ser.write(('S' + str(Inference.DIRECTION) + str(Inference.HIGH_EIGHT) + str(0) + str(Inference.LOW_EIGHT) + 'E').encode("utf-8"))

                elif Inference.LOW_EIGHT / 1 >= 1:
                    self.ser.write(('S' + str(Inference.DIRECTION) + str(Inference.HIGH_EIGHT) + str(0) + str(0) + str(Inference.LOW_EIGHT) + 'E').encode("utf-8"))

                else:
                    self.ser.write(('S' + str(2) + str(0) + str(0) + str(0) + str(0) + 'E').encode("utf-8"))
            except:
                self.ser.close()
                print('Serial Send Data Error')
                Interactive_serial.serial_connection(self)
                
    # 串口接收数据
    # def receive_data(self):
    #     while True:
    #         time.sleep(0.05)
    #         try:
    #             data = self.ser.read(3)
    #             if data == b'\x03\x03\x03' or data == b'\x01\x01\x01':
    #                 Inference.TARGET_X = 480  #空接 不抬升500 抬升480 
    #                 Inference.FLAG = 1
    #                 # print(data)
    #             if data == b'\x02\x02\x02':
    #                 Inference.TARGET_X = 415  #资源岛
    #                 Inference.FLAG = 0
    #                 # print(data)
    #             print(data)
    #         except:                
    #             self.ser.close()
    #             print('Serial Send Data Error')
    #             Inference.serial_connection(self)
                