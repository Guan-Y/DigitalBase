import serial
from scipy import signal
import time
import datetime

PORT = 'COM11'
BAUDRATE = 460800
FRAME_HEADER = [0x22, 0x22]

SHOE_TYPE_7_FFONT = 58.8/(5+(32-1)*0.5)
SHOE_TYPE_7_BACK = 58.8/(5+(30-1)*0.5)
R0 = 10000

SSL_connect = False
SSR_connect = False
ALL_SS_connect = False

PPG1_connect = False
PPG2_connect = False
ALL_PPG_connect = False

ECG_connect = False

PPG1_CNT = 0
PPG1_update = False
PPG1_List = []

PPG2_CNT = 0
PPG2_update = False
PPG2_List = []

SSL_CNT = 0
SSL_update = False
SSL_List = []

SSR_CNT = 0
SSR_update = False
SSR_List = []

ECG_CNT = 0
ECG_update = False
ECG_List = []
RESP_List = []
ECG_origin = []

#file buffer
PPG_Time_Data_List = []
Max_Buf_Len = 300

def Port_Detect():
    pass

def Port_Open():
    global ser
    ser.open()

def Port_Close():
    global ser
    ser.close()


def Get_Connection_Status():
    pass

def get_R(adc_h,adc_l):
    adc = (adc_h << 8) | adc_l
    R = adc * R0 / (3.3/4/0.825*4095-adc)
    return R

def get_Pressure(R,idx):
    if idx <= 4:
        return SHOE_TYPE_7_FFONT * 100000 / R
    elif idx > 4 and idx <= 8:
        return SHOE_TYPE_7_BACK * 100000 / R
    else:
        return 0

def butterBandPassFilter(lowcut, highcut, samplerate, order):
    "生成巴特沃斯带通滤波器"
    semiSampleRate = samplerate*0.5
    low = lowcut / semiSampleRate
    high = highcut / semiSampleRate
    b,a = signal.butter(order,[low,high],btype='bandpass')
    print("bandpass:","b.shape:",b.shape,"a.shape:",a.shape,"order=",order)
    print("b=",b)
    print("a=",a)
    return b,a

def Get_Serial_Data():
    global PPG1_List,PPG2_List,SSL_List,SSR_List,ECG_List,RESP_List,ECG_origin
    global PPG1_CNT,PPG2_CNT,SSL_CNT,SSR_CNT,ECG_CNT
    global PPG1_update,PPG2_update,SSL_update,SSR_update,ECG_update
    global ALL_SS_connect,SSL_connect,SSR_connect
    global ALL_PPG_connect,PPG1_connect,PPG2_connect
    global ECG_connect
    ser = serial.Serial(PORT,BAUDRATE)
    b, a = butterBandPassFilter(0.8, 70, 250, order=5)

    while ser.isOpen():
        #if(ser.isOpen() != True):
            #continue
        if ser.read(1)[0] == FRAME_HEADER[0]:
            if ser.read(1)[0] == FRAME_HEADER[1]:
                data_src = ser.read(1)[0]
                data_idx = ser.read(1)[0]
                data_len = ser.read(1)[0]
                data = ser.read(data_len)
                # print(data_src,data_idx,data.hex(' ',1))
                if data_src == 0:
                    if PPG1_connect:
                        PPG = data[7] << 24 | data[6] << 16 | data[5] << 8 | data[4]
                        PPG1_List.append(PPG)
                        PPG1_CNT = PPG1_CNT + 1
                        PPG1_update = True
                    else:
                        PPG1_connect = True

                elif data_src == 1:
                    if PPG2_connect:
                        PPG = data[7] << 24 | data[6] << 16 | data[5] << 8 | data[4]
                        PPG2_List.append(PPG)
                        PPG2_CNT = PPG2_CNT + 1
                        PPG2_update = True
                    else:
                        PPG2_connect = True

                        #t = time.time()
                        #nowtime = lambda: int(t * 1000)
                        #formatted_date = datetime.datetime.fromtimestamp(nowtime() / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
                        #print(formatted_date)

                        fbuf = [0, 0]
                        #fbuf[0] = formatted_data

                elif data_src == 2:
                    if SSL_connect:
                        P = 0
                        for i in range(8):
                            R = get_R(data[i * 2], data[i * 2 + 1])
                            P = P + get_Pressure(R, i + 1)
                        SSL_List.append(P)
                        SSL_CNT = SSL_CNT + 1
                        SSL_update = True
                    else:
                        SSL_connect = True
                elif data_src == 3:
                    if SSR_connect:
                        P = 0
                        for i in range(8):
                            R = get_R(data[i * 2], data[i * 2 + 1])
                            P = P + get_Pressure(R, i + 1)
                        SSR_List.append(P)
                        SSR_CNT = SSR_CNT + 1
                        SSR_update = True
                    else:
                        SSR_connect = True
                elif data_src == 4:
                    if ECG_connect:
                        ECG_CNT = ECG_CNT + 20
                        ECG_update = True
                        for i in range(20):
                            RESP = (data[i*6] << 16) | (data[i*6+1]<<8) | (data[i*6+2])
                            ECG = (data[i*6+3]<<16) | (data[i*6+4]<<8) | (data[i*6+5])

                            if RESP >= (1<<23):
                                RESP = RESP - (1<<24)
                            if ECG >= (1<<23):
                                ECG = ECG - (1<<24)
                            ECG_origin.append(ECG)
                            if ECG_CNT > 20:
                                ECG_origin = ECG_origin[-10:]
                                x = signal.lfilter(b,a,ECG_origin)
                                ECG = x[-1]
                            RESP_List.append(RESP)
                            ECG_List.append(ECG)
                    else:
                        ECG_connect = True

