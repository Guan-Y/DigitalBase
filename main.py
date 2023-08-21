import random
import sys
import upper_machine
import PyQt5
import pyqtgraph as pg
from PyQt5.Qt import QApplication
from PyQt5 import QtWidgets
import MySerial
from threading import Thread
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import time, datetime


PLOT_RANGE = 200
X = [i for i in range(PLOT_RANGE)]

PPG1_Plot_List = []
PPG2_Plot_List = []
SSL_Plot_List = []
SSR_Plot_List = []
ECG_Plot_List = []
RESP_Plot_List = []

DEV_ID_PPG1 = 0
DEV_ID_PPG2 = 1
DEV_ID_SSL = 2
DEV_ID_SSR = 3
DEV_ID_ECG = 4


class Update_Parameter_Thread(QThread):
    def run(self):
        Calculate_Parameters()
class Serial_Thread(QThread):
    def run(self):
        MySerial.Get_Serial_Data()

class MainWindow(upper_machine.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.graphwidget_ppg1.setTitle("PPG1")
        self.graphwidget_ppg2.setTitle("PPG2")
        self.graphwidget_ssl.setTitle("Smart Shoe L")
        self.graphwidget_ssr.setTitle("Smart Shoe R")
        self.graphwidget_ecg.setTitle("ECG")
        self.graphwidget_resp.setTitle("RESP")

        self.serial_thread = Serial_Thread()
        #self.show_parameter_thread = Update_Parameter_Thread()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.ui_update)
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.connect_status_update)

    def startTimer(self, interval):
        self.ui_timer.start(interval)
        self.connection_timer.start(2000)



    def connect_status_update(self):
        if MySerial.PPG1_connect == True:
            window.pushButton_ppg1connect.setText("已连接")
        else:
            window.pushButton_ppg1connect.setText("未连接")

        if MySerial.PPG2_connect == True:
            window.pushButton_ppg2connect.setText("已连接")
        else:
            window.pushButton_ppg2connect.setText("未连接")

        if MySerial.SSL_connect == True:
            window.pushButton_sslconnect.setText("已连接")
        else:
            window.pushButton_sslconnect.setText("未连接")

        if MySerial.SSR_connect == True:
            window.pushButton_ssrconnect.setText("已连接")
        else:
            window.pushButton_ssrconnect.setText("未连接")

        if MySerial.ECG_connect == True:
            window.pushButton_ecgconnect.setText("已连接")
        else:
            window.pushButton_ecgconnect.setText("未连接")

        if MySerial.ECG_connect == True:
            window.pushButton_respconnect.setText("已连接")
        else:
            window.pushButton_respconnect.setText("未连接")


    def ui_update(self):
        ppg1.Parameter_String_Load()
        ppg2.Parameter_String_Load()
        ssl.Parameter_String_Load()
        ssr.Parameter_String_Load()
        ecg.Parameter_String_Load()
        resp.Parameter_String_Load()

        window.label_datarate_ppg1.setText(ppg1.str_datarate)
        window.label_data_ppg1.setText(ppg1.str_dataamount)
        window.label_delay_ppg1.setText(ppg1.str_delay)

        window.label_datarate_ppg2.setText(ppg2.str_datarate)
        window.label_data_ppg2.setText(ppg2.str_dataamount)
        window.label_delay_ppg2.setText(ppg2.str_delay)

        window.label_datarate_ssl.setText(ssl.str_datarate)
        window.label_data_ssl.setText(ssl.str_dataamount)
        window.label_delay_ssl.setText(ssl.str_delay)

        window.label_datarate_ssr.setText(ssr.str_datarate)
        window.label_data_ssr.setText(ssr.str_dataamount)
        window.label_delay_ssr.setText(ssr.str_delay)

        window.label_datarate_ecg.setText(ecg.str_datarate)
        window.label_data_ecg.setText(ecg.str_dataamount)
        window.label_delay_ecg.setText(ecg.str_delay)

        window.label_datarate_resp.setText(resp.str_datarate)
        window.label_data_resp.setText(resp.str_dataamount)
        window.label_delay_resp.setText(resp.str_delay)


    def plot_ppg1(self, x, y):
        self.graphwidget_ppg1.clear()
        self.graphwidget_ppg1.plot(x, y)

    def plot_ppg2(self, x, y):
        self.graphwidget_ppg2.clear()
        self.graphwidget_ppg2.plot(x, y)

    def plot_ssl(self, x, y):
        self.graphwidget_ssl.clear()
        self.graphwidget_ssl.plot(x, y)

    def plot_ssr(self, x, y):
        self.graphwidget_ssr.clear()
        self.graphwidget_ssr.plot(x, y)

    def plot_ecg(self, x, y):
        self.graphwidget_ecg.clear()
        self.graphwidget_ecg.plot(x, y)

    def plot_resp(self, x, y):
        self.graphwidget_resp.clear()
        self.graphwidget_resp.plot(x, y)


class BLE_Device_Interface():
    def __init__(self, device_ID,data_pack_len=20):
        self.ID = device_ID
        self.time_record_begin = int(time.time()*1000)
        self.time_record_end = int(time.time()*1000)
        self.trans_data_rate = 0    #比特率，按收到的数据包长计算（除掉帧头帧尾）
        self.total_data_amount = 0
        self.delay = 0
        self.data_package_len = data_pack_len
        self.str_datarate = "{:>6}".format("Kb/s")
        self.str_dataamount = "{:>6}".format("Kb")
        self.str_delay = "{:>6}".format("ms")

    def Parameter_Update(self, data_amount):
        self.time_record_end = int(time.time() * 1000)
        interval = self.time_record_end - self.time_record_begin  # ms
        self.delay = interval
        # 每个数据包总共n个Bytes
        self.trans_data_rate = self.data_package_len * (data_amount - self.total_data_amount) * 1000 / (interval+1)
        self.total_data_amount = data_amount
        self.time_record_begin = self.time_record_end

    def Parameter_String_Load(self):
        self.str_datarate = "{:^6.2f} {:>4}".format(self.trans_data_rate / 1000, "Kb/s")
        self.str_dataamount = "{:^6.2f} {:>4}".format(self.total_data_amount * self.data_package_len / 1000, "Kb")
        self.str_delay = "{:^4} {:>4}".format(self.delay, "ms")

    def BLE_Connection_On(self):
        pass

    def BLE_Connection_Off(self):
        pass

    def Data_Receive_Enable(self):
        pass

    def Data_Receive_Disable(self):
        pass

    def BLE_Set_MAC_Addr(self):
        pass


def plotData():
    global PPG1_Plot_List
    temp = [random.randint(20,30) for _ in range(PLOT_RANGE)]
    if (MySerial.PPG1_update):
        MySerial.PPG1_update = False
        if (MySerial.PPG1_CNT > PLOT_RANGE):
            PPG1_Plot_List = MySerial.PPG1_List[-PLOT_RANGE:]
            #MySerial.PPG1_List = MySerial.PPG1_List[-PLOT_RANGE:]
            window.graphwidget_ppg1.setRange(yRange=[min(PPG1_Plot_List[-PLOT_RANGE:]), max(PPG1_Plot_List[-PLOT_RANGE:])])
        else:
            PPG1_Plot_List = MySerial.PPG1_List
            PPG1_Plot_List = PPG1_Plot_List + [sum(PPG1_Plot_List) / len(PPG1_Plot_List) for _ in range(PLOT_RANGE - len(PPG1_Plot_List))]

        t = time.time()
        nowtime = lambda: int(t * 1000)
        formatted_date = datetime.datetime.fromtimestamp(nowtime() / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
        #print(formatted_date)

        #print(PPG1_Plot_List)
        #PPG1_Plot_List = MySerial.PPG1_List

        window.plot_ppg1(X, PPG1_Plot_List[0:PLOT_RANGE])


    if (MySerial.PPG2_update):
        global PPG2_Plot_List
        MySerial.PPG2_update = False
        if (MySerial.PPG2_CNT > PLOT_RANGE):
            PPG2_Plot_List = MySerial.PPG2_List[-PLOT_RANGE:]
            window.graphwidget_ppg2.setRange(yRange=[min(PPG2_Plot_List[-PLOT_RANGE:]), max(PPG2_Plot_List[-PLOT_RANGE:])])
        else:
            PPG2_Plot_List = MySerial.PPG2_List
            PPG2_Plot_List = PPG2_Plot_List + [sum(PPG2_Plot_List) / len(PPG2_Plot_List) for _ in range(PLOT_RANGE - len(PPG2_Plot_List))]

        #PPG2_Plot_List = MySerial.PPG2_List
        t = time.time()
        nowtime = lambda: int(t * 1000)
        formatted_date = datetime.datetime.fromtimestamp(nowtime() / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
        #print(formatted_date)
        #print(PPG2_Plot_List)
        #print(MySerial.PPG2_List)
        window.plot_ppg2(X, PPG2_Plot_List[0:PLOT_RANGE])


    if (MySerial.SSL_update):
        global SSL_Plot_List
        MySerial.SSL_update = False
        if (MySerial.SSL_CNT > PLOT_RANGE):
            SSL_Plot_List = MySerial.SSL_List[-PLOT_RANGE:]
        else:
            SSL_Plot_List = MySerial.SSL_List
            SSL_Plot_List = SSL_Plot_List + [sum(SSL_Plot_List) / len(SSL_Plot_List) for _ in
                                               range(PLOT_RANGE - len(SSL_Plot_List))]

        window.plot_ssl(X, SSL_Plot_List)


    if (MySerial.SSR_update):
        global SSR_Plot_List
        MySerial.SSR_update = False
        if (MySerial.SSR_CNT > PLOT_RANGE):
            SSR_Plot_List = MySerial.SSR_List[-PLOT_RANGE:]
        else:
            SSR_Plot_List = MySerial.SSR_List
            SSR_Plot_List = SSR_Plot_List + [sum(SSR_Plot_List) / len(SSR_Plot_List) for _ in
                                             range(PLOT_RANGE - len(SSR_Plot_List))]
        window.plot_ssr(X, SSR_Plot_List)


    if (MySerial.ECG_update):
        global ECG_Plot_List
        global RESP_Plot_List
        MySerial.ECG_update = False
        if (MySerial.ECG_CNT > PLOT_RANGE):
            window.graphwidget_ecg.setRange(yRange=[min(ECG_Plot_List[-PLOT_RANGE:]), max(ECG_Plot_List[-PLOT_RANGE:])])
            window.graphwidget_resp.setRange(yRange=[min(RESP_Plot_List[-PLOT_RANGE:]), max(RESP_Plot_List[-PLOT_RANGE:])])
            ECG_Plot_List = MySerial.ECG_List[-PLOT_RANGE:]
            RESP_Plot_List = MySerial.RESP_List[-PLOT_RANGE:]
        elif (MySerial.ECG_CNT > 40):
            pass
            #window.graphwidget_ecg.setRange(xRange=[40, PLOT_RANGE], yRange=[min(ECG_Plot_List[40:PLOT_RANGE]), max(ECG_Plot_List[40:PLOT_RANGE])])
        else:
            ECG_Plot_List = MySerial.ECG_List
            ECG_Plot_List = ECG_Plot_List + [sum(ECG_Plot_List) / len(ECG_Plot_List) for _ in
                                             range(PLOT_RANGE - len(ECG_Plot_List))]
            RESP_Plot_List = MySerial.RESP_List
            RESP_Plot_List = RESP_Plot_List + [sum(RESP_Plot_List) / len(RESP_Plot_List) for _ in
                                             range(PLOT_RANGE - len(RESP_Plot_List))]

        window.plot_ecg(X, ECG_Plot_List)
        window.plot_resp(X, RESP_Plot_List)



def Calculate_Parameters():
    #ppg2.Parameter_Update(MySerial.PPG2_CNT)

    i = random.randint(0, 5)
    if(i == 0):
        ppg2.Parameter_Update(MySerial.PPG2_CNT)
        return

    if(i == 1):
        ppg1.Parameter_Update(MySerial.PPG1_CNT)
        return

    if(i == 2):
        ssl.Parameter_Update(MySerial.SSL_CNT)
        return

    if(i == 3):
        ssr.Parameter_Update(MySerial.SSR_CNT)
        return

    if(i == 4):
        ecg.Parameter_Update(MySerial.ECG_CNT)
        return

    if(i == 5):
        resp.Parameter_Update(MySerial.ECG_CNT)
        return

    return



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    ppg1 = BLE_Device_Interface(DEV_ID_PPG1)
    ppg2 = BLE_Device_Interface(DEV_ID_PPG2)
    ssl = BLE_Device_Interface(DEV_ID_SSL)
    ssr = BLE_Device_Interface(DEV_ID_SSR)
    ecg = BLE_Device_Interface(DEV_ID_ECG)
    resp = BLE_Device_Interface(DEV_ID_ECG)

    timer = pg.QtCore.QTimer()
    timer.timeout.connect(plotData)  # 定时器结束后调用plotData函数
    timer.start(50)  # 多少ms调用一次

    timer1 = pg.QtCore.QTimer()
    timer1.timeout.connect(Calculate_Parameters)  # 定时器结束后调用plotData函数
    timer1.start(10)  # 多少ms调用一次


    window.serial_thread.start()
    window.startTimer(300)

    sys.exit(app.exec_())
