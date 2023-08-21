import pyqtgraph as pg
import serial
from threading import Thread
from scipy import signal
import time
import datetime

# 全局变量区
PORT = 'COM14'
BAUDRATE = 115200
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

def get_serial_data():
    global PPG1_List,PPG2_List,SSL_List,SSR_List,ECG_List,RESP_List,ECG_origin
    global PPG1_CNT,PPG2_CNT,SSL_CNT,SSR_CNT,ECG_CNT
    global PPG1_update,PPG2_update,SSL_update,SSR_update,ECG_update
    global ALL_SS_connect,SSL_connect,SSR_connect
    global ALL_PPG_connect,PPG1_connect,PPG2_connect
    ser = serial.Serial(PORT,BAUDRATE)
    while ser.isOpen():
        if ser.read(1)[0] == FRAME_HEADER[0]:
            if ser.read(1)[0] == FRAME_HEADER[1]:
                data_src = ser.read(1)[0]
                data_idx = ser.read(1)[0]
                data_len = ser.read(1)[0]
                data = ser.read(data_len)
                # print(data_src,data_idx,data.hex(' ',1))
                if data_src == 0 or data_src == 1:
                    if PPG1_connect or PPG2_connect:
                        t = time.time()
                        nowtime = lambda: int(t * 1000)
                        formatted_date = datetime.datetime.fromtimestamp(nowtime() / 1000).strftime(
                            '%Y-%m-%d %H:%M:%S.%f')
                        print(formatted_date)

                        fbuf = [0, 0]
                        fbuf[0] = formatted_date

                        PPG = data[7]<<24 | data[6]<<16 | data[5]<<8 | data[4]
                        fbuf[1] = PPG

                        if data_src == 0:
                            PPG1_List.append(PPG)
                            PPG1_CNT = PPG1_CNT + 1
                            PPG1_update = True

                        elif data_src == 1:
                            PPG2_List.append(PPG)
                            PPG2_CNT = PPG2_CNT + 1
                            PPG2_update = True
                            PPG_Time_Data_List.append(fbuf)

                        if len(PPG_Time_Data_List) > Max_Buf_Len:
                            pass
                            #print(PPG_Time_Data_List)


                    else:
                        if data_src == 0:
                            PPG1_connect = True
                        elif data_src == 1:
                            PPG2_connect = True
                        if PPG1_connect and PPG2_connect:
                            PPG1_connect = False
                            PPG2_connect = False
                            ALL_PPG_connect = True
                            ser.flushInput()
                            print("清空缓冲区")
                elif data_src == 2 or data_src == 3:
                    if ALL_SS_connect:
                        P = 0
                        for i in range(8):
                            R = get_R(data[i*2],data[i*2+1])
                            P = P + get_Pressure(R,i+1)
                        if data_src == 2:
                            SSL_List.append(P)
                            SSL_CNT = SSL_CNT + 1
                            SSL_update = True
                        elif data_src == 3:
                            SSR_List.append(P)
                            SSR_CNT = SSR_CNT + 1
                            SSR_update = True
                    else:
                        if data_src == 2:
                            SSL_connect = True
                        elif data_src == 3:
                            SSR_connect = True
                        if SSL_connect and SSR_connect:
                            SSL_connect = False
                            SSR_connect = False
                            ALL_SS_connect = True
                            ser.flushInput()
                            print("清空缓冲区")
                elif data_src == 4:
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
                            # print(ECG)
def plotData():
    global PPG1_update,PPG2_update,SSL_update,SSR_update,ECG_update
    global PPG1_List,PPG2_List,SSL_List,SSR_List,ECG_List,RESP_List,ECG_origin
    if(PPG1_update):
        PPG1_update = False
        if(PPG1_CNT>500):
            PPG1_List = PPG1_List[-500:]
            p1.setRange(yRange=[min(PPG1_List[-500:]),max(PPG1_List[-500:])])
        line1.setData(PPG1_List)   

    if(PPG2_update):
        PPG2_update = False
        if(PPG2_CNT>500):
            PPG2_List = PPG2_List[-500:]
            p2.setRange(yRange=[min(PPG2_List[-500:]),max(PPG2_List[-500:])])
        line2.setData(PPG2_List)

    if(SSL_update):
        SSL_update = False
        if(SSL_CNT>300):
            SSL_List = SSL_List[-300:]
        line3.setData(SSL_List)   

    if(SSR_update):
        SSR_update = False
        if(SSR_CNT>300):
            SSR_List = SSR_List[-300:]
        line4.setData(SSR_List)

    if(ECG_update):
        ECG_update = False
        if(ECG_CNT>1000):
            p5.setRange(yRange=[min(ECG_List[-1000:]),max(ECG_List[-1000:])])
            p6.setRange(yRange=[min(RESP_List[-1000:]),max(RESP_List[-1000:])])
            ECG_List = ECG_List[-1000:]
            RESP_List = RESP_List[-1000:]
        elif(ECG_CNT>40):
            p5.setRange(xRange=[40, ECG_CNT],yRange=[min(ECG_List[40:ECG_CNT]),max(ECG_List[40:ECG_CNT])])
        line5.setData(ECG_List)
        line6.setData(RESP_List)

if __name__ == "__main__":

    # 设置窗口参数
    app = pg.mkQApp()   #建立app
    win = pg.GraphicsLayoutWidget(show=True)  #建立窗口
    win.setBackground('w')  # 设置背景
    win.resize(1000, 700)   # 设置窗口大小

    # 创建三个子图
    p1 = win.addPlot(title='PPG1')
    line1 = p1.plot(pen=pg.mkPen(color='b',width=2))
    win.nextRow()
    p2 = win.addPlot(title='PPG2')
    line2 = p2.plot(pen=pg.mkPen(color='b',width=2))
    win.nextRow()

    p3 = win.addPlot(title='SSL')
    p3.setRange(yRange=[0, 1800])
    line3 = p3.plot(pen=pg.mkPen(color='b',width=2))
    win.nextRow()
    p4 = win.addPlot(title='SSR')
    p4.setRange(yRange=[0, 1800])
    line4 = p4.plot(pen=pg.mkPen(color='b',width=2))
    win.nextRow()

    p5 = win.addPlot(title='ECG')
    line5 = p5.plot(pen=pg.mkPen(color='b',width=2))
    win.nextRow()
    p6 = win.addPlot(title='RESP')
    line6 = p6.plot(pen=pg.mkPen(color='b',width=2))

    b,a = butterBandPassFilter(0.8,70,250,order=5)

    # 创建ch线程
    thread1 = Thread(target = get_serial_data)
    thread1.start()

    # 启动qt定时器
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(plotData) #定时器结束后调用plotData函数
    timer.start(1)  #多少ms调用一次

    app.exec_()