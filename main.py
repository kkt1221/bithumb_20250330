import logging
import logging.handlers
import os
import sys
from datetime import datetime
from tkinter import Tk
from tkinter import messagebox as msg

from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from bithumbApi import trading_api, exchange_api, quotation_api





class Thread_run(QThread):
    # parent = 메인위젯을 상속 받음.
    # def __init__(self, parent):
    #     super().__init__(parent)

    def run(self):
        logger.info("THREAD START")
        trading_api.speedTradingStart6()


# class LogStringHandler(logging.Handler):
#     def __init__(self, target_wiget):
#         super(LogStringHandler, self).__init__()
#         self.target_wiget = target_wiget
#
#     def emit(self, record):
#         self.target_wiget.append(record.asctime + '--' + record.getMessage())


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        global logger  # 전체에서 로그를 사용하기 위해 global로 선언을 해줌(전역 변수)
        logger = logging.getLogger('tradingLogger')  # 로그 인스턴스를 만든다
        self.set_logger()  # 로그 인스턴스 환경 설정을 셋팅함

        self.targetPriceList = {}  # 매수 목표가 리스트
        self.selectCoinNameList = []  # 코인종목 리스트

        self.lbl1 = QLabel('종목 선택', self)
        self.cb1 = QComboBox(self)
        self.insertAllBtn = QPushButton('전체추가', self)
        self.insertBtn = QPushButton('추가', self)
        self.deleteBtn = QPushButton('삭제', self)
        self.te1 = QTextEdit('', self)
        self.lbl3 = QLabel('현재 보유 원화', self)
        self.qle1 = QLineEdit(self)
        self.sellCoinBtn = QPushButton('선택종목전액매도', self)
        self.buyAllBtn = QPushButton('선택종목전액매수', self)
        self.sellAllBtn = QPushButton('보유종목전체매도', self)
        # self.tb1 = QTextBrowser(self)
        self.lbl7 = QLabel('호가', self)
        self.lbl8 = QLabel('수량', self)
        self.qle7 = QLineEdit(self)
        self.qle8 = QLineEdit(self)
        self.buyStartBtn3 = QPushButton('선택종목지정가매도', self)
        self.buyStopBtn3 = QPushButton('선택종목지정가매수', self)
        self.lbl9 = QLabel('보유수량', self)
        self.qle9 = QLineEdit(self)
        self.lbl10 = QLabel('평단', self)
        self.qle10 = QLineEdit(self)
        self.lbl11 = QLabel('분할시작가격', self)
        self.qle11 = QLineEdit(self)
        self.lbl12 = QLabel('분할매도가격', self)
        self.qle12 = QLineEdit(self)
        self.lbl13 = QLabel('거래간격(호가)', self)
        self.qle13 = QLineEdit(self)
        self.sellBtn1 = QPushButton('분할매도', self)
        self.fileSave = QPushButton('파일저장', self)
        self.sellBtn2 = QPushButton('자동단타매매시작', self)
        self.sellBtn3 = QPushButton('자동단타매매종료', self)

        # log = logging.getLogger('tradingLogger')  # 로그 객체
        # log.addHandler(LogStringHandler(self.tb1))  # 핸들러 tb1연동

        self.initUI()

    def initUI(self):
        self.setWindowTitle('BITHUMB 단타매매')
        window_ico = resource_path('logo.ico')
        self.setWindowIcon(QIcon(window_ico))

        self.resize(540, 290)
        self.center()
        self.selectTickers()
        self.show()

    # 앱 창 중앙 정렬
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 매수 종목 선택
    def selectTickers(self):

        # 로그 사용을 위하 세팅
        trading_api.logger = logger
        exchange_api.logger = logger
        quotation_api.loggr = logger

        # 업비트 인증키 세팅 파일명 세팅
        #trading_api.ipAddressFile = trading_api.getIpConfig()
        trading_api.ipAddressFile = resource_path('bithumb_home.txt')

        # 원화마켓에 등록된 코인 전체 목록 세팅
        trading_api.getMarketCoins()

        # 원화마켓 등록된 코인 한글 목록
        tickers = trading_api.getKrwMarketTickers()

        # 현재 원화마켓 보유중인 코인 리스트
        trading_api.myKrwCoinHoldList()

        # 종목 선택 레이블
        self.lbl1.move(10, 20)

        # 종목 선택 콤보박스
        for i in tickers:
            self.cb1.addItem(i)

        self.cb1.cursor()
        self.cb1.move(70, 16)
        self.cb1.resize(200, 20)
        self.cb1.activated[str].connect(self.setSelectCoinChecked)

        # 전체 추가 버튼
        self.insertAllBtn.move(10, 42)
        self.insertAllBtn.resize(80, 24)
        self.insertAllBtn.clicked.connect(self.insertAllCoinName)

        # 추가 버튼
        self.insertBtn.move(100, 42)
        self.insertBtn.resize(80, 24)
        self.insertBtn.clicked.connect(self.insertCoinName)

        # 삭제 버튼
        self.deleteBtn.move(190, 42)
        self.deleteBtn.resize(80, 24)
        self.deleteBtn.clicked.connect(self.deleteCoinName)

        # 매매 진행 종목 노출 텍스트 박스
        self.te1.setAcceptRichText(False)
        self.te1.move(10, 70)
        self.te1.resize(260, 210)

        # 현재 보유 원화 레이블
        self.lbl3.move(280, 18)

        # 현재 보유 원화 텍스트
        self.qle1.move(370, 12)
        self.qle1.resize(160, 24)
        self.qle1.setReadOnly(True)
        krwTarget = trading_api.getKrwTarget()
        self.qle1.setText(str(krwTarget))

        # 선택종목 전액 매도 버튼
        self.sellCoinBtn.move(280, 42)
        self.sellCoinBtn.resize(120, 24)
        self.sellCoinBtn.clicked.connect(self.sellSelectCoin)

        # 선택종목 전액 매수 버튼
        self.buyAllBtn.move(410, 42)
        self.buyAllBtn.resize(120, 24)
        self.buyAllBtn.clicked.connect(self.buyAllCoin)

        # 보유종목 전체 매도 버튼
        self.sellAllBtn.move(280, 72)
        self.sellAllBtn.resize(250, 24)
        self.sellAllBtn.clicked.connect(self.sellAllCoin)

        # # 로그 출력 텍스트 브라우저
        # self.tb1.move(10, 260)
        # self.tb1.resize(520, 160)
        # self.tb1.setAcceptRichText(True)
        # self.tb1.setOpenExternalLinks(True)

        # 지정가 가격
        self.lbl7.move(284, 108)

        # 지정가 가격 텍스트
        self.qle7.move(318, 102)
        self.qle7.resize(80, 22)
        self.qle7.setText("0")

        # 지정가 수량
        self.lbl8.move(410, 108)

        # 지정가 수량 텍스트
        self.qle8.move(450, 102)
        self.qle8.resize(80, 22)
        self.qle8.setText("0")

        # 선택종목 지정가 매도 버튼
        self.buyStartBtn3.move(280, 130)
        self.buyStartBtn3.resize(120, 24)
        self.buyStartBtn3.clicked.connect(self.sellLimitPriceCoin)

        # 선택종목 지정가 매수 버튼
        self.buyStopBtn3.move(410, 130)
        self.buyStopBtn3.resize(120, 24)
        self.buyStopBtn3.clicked.connect(self.buyLimitPriceCoin)

        # 보유 수량
        self.lbl9.move(280, 166)

        # 보유수량 텍스트
        self.qle9.move(330, 160)
        self.qle9.resize(70, 22)
        self.qle9.setReadOnly(True)
        self.qle9.setText("0")

        # 평균가
        self.lbl10.move(410, 166)

        # 평균가 텍스트
        self.qle10.move(440, 160)
        self.qle10.resize(90, 22)
        self.qle10.setReadOnly(True)
        self.qle10.setText("0")

        #  분할 시작 가격
        self.lbl11.move(280, 196)

        # 거래수량 텍스트
        self.qle11.move(350, 190)
        self.qle11.resize(50, 22)
        self.qle11.setText("0")

        # 분할 갯수
        self.lbl12.move(410, 196)

        # 분할 매도 가격 텍스트
        self.qle12.move(460, 190)
        self.qle12.resize(70, 22)
        self.qle12.setText("20000")

        #  거래 간격
        self.lbl13.move(280, 226)

        # 거래 간격 텍스트
        self.qle13.move(368, 220)
        self.qle13.resize(32, 22)
        self.qle13.setText("1")

        # 추가종목분할매도 버튼
        self.sellBtn1.move(410, 220)
        self.sellBtn1.resize(60, 24)
        self.sellBtn1.clicked.connect(self.sellAllShareCoin)

        # 파일저장 버튼
        self.fileSave.move(470, 220)
        self.fileSave.resize(60, 24)
        self.fileSave.clicked.connect(self.fileSaveVolume)

        # 자동 단타 매매시작 버튼
        self.sellBtn2.move(280, 252)
        self.sellBtn2.resize(120, 24)
        self.sellBtn2.clicked.connect(self.startTrading)

        # 자동 단타 매매종료 버튼
        self.sellBtn3.move(410, 252)
        self.sellBtn3.resize(120, 24)
        self.sellBtn3.clicked.connect(self.stopTrading)

        self.setMyCurrentBalance()

    # 선택종목 보유수량, 매수평균가 노출
    def setMyCurrentBalance(self):
        isYn = trading_api.isCoinHoldYn(self.cb1.currentText())
        if isYn is True:
            krwCoinBalance = trading_api.getKrwCoinTarget(self.cb1.currentText(), "balance")
            krwCoinLocked = trading_api.getKrwCoinTarget(self.cb1.currentText(), "locked")
            krwCoinBalance = str(float(krwCoinBalance) + float(krwCoinLocked))
            self.qle9.setText(krwCoinBalance)
            krwCoinPrice = trading_api.getKrwCoinTarget(self.cb1.currentText(), "avg_buy_price")
            self.qle10.setText(krwCoinPrice)
            krwCurrentPrice = trading_api.gatCurrentPrice(self.cb1.currentText())
            self.qle11.setText(krwCurrentPrice)
            trading_api.setWaitPriceList(self.cb1.currentText())
        else:
            self.qle9.setText("")
            self.qle10.setText("")

    # 콤보박스 선택시  호출
    def setSelectCoinChecked(self):
        self.setMyCurrentBalance()

    # 전체 추가 버튼 클릭 시 리스트에 추가
    def insertAllCoinName(self):

        tickers = []
        # 원화마켓 등록된 코인 전체 목록
        tickers = trading_api.getKrwMarketTickers()
        for i in tickers:
            if i not in self.selectCoinNameList:
                isYn = trading_api.isCoinHoldYn(i)
                if isYn is True:
                    self.selectCoinNameList.append(i)

        # 추가된 리스트를 전달
        trading_api.mySelectCoinList(self.selectCoinNameList)

        # 화면 갱신
        self.showCoinList()
        self.setMyCurrentBalance()

    # 추가 버튼 클릭 시 리스트에 추가
    def insertCoinName(self):
        if self.cb1.currentText() in self.selectCoinNameList:
            self.errMessage("이미 추가된 종목 입니다")
        else:
            isYn = trading_api.isCoinHoldYn(self.cb1.currentText())
            if isYn is True:
                # 리스트에서 코인 추가
                self.selectCoinNameList.append(self.cb1.currentText())

                # 추가된 리스트를 전달
                trading_api.mySelectCoinList(self.selectCoinNameList)

                # 사용자 입력 데이터 저장
                self.setUserData()

                # 화면 갱신
                self.showCoinList()
                self.setMyCurrentBalance()
            else:
                self.errMessage("미보유 종목 입니다")

    userSettingData = []

    # 사용자 설정값 리스트 추가
    def setUserData(self):
        coinName = self.cb1.currentText()
        sellRange = self.qle13.text()  # 거래간격
        sellStartPrice = self.qle11.text()  # 분할시작가격
        sellSharePrice = self.qle12.text()  # 분할매도가격
        currentBalance = self.qle9.text()  # 현재 보유수량
        sellBalance = float(sellSharePrice) / float(sellStartPrice)  # 분할 매도 수량
        sellMaxCount = int(float(currentBalance) / float(sellBalance))
        currentPrice = trading_api.gatCurrentPrice(self.cb1.currentText())

        if len( self.userSettingData) != 0:
            self.userSettingData.clear()

        self.userSettingData.append(
            {'coinName': coinName, 'sellRange': sellRange, 'sellStartPrice': sellStartPrice, 'sellSharePrice': sellSharePrice ,
             'currentBalance': currentBalance, 'sellBalance': sellBalance, 'sellMaxCount': sellMaxCount, 'currentPrice': currentPrice})

        # 사용자 입력 가격 전달
        trading_api.myTargetPriceList = self.userSettingData

    # 삭제 버튼 클릭 시 리스트에서 삭제
    def deleteCoinName(self):
        # 콤보박스 선택된 코인이 존재할 경우
        if self.cb1.currentText() in self.selectCoinNameList:
            # 리스트에서 코인 삭제
            self.selectCoinNameList.remove(self.cb1.currentText())

            # 삭제된 리스트를 전달
            trading_api.mySelectCoinList(self.selectCoinNameList)

            # 사정자 입력정보 삭제
            self.removeUserData()

            # 사용자 입력 정보 전달
            trading_api.myTargetPriceList = self.userSettingData

            # 화면 갱신
            self.showCoinList()
            self.setMyCurrentBalance()

        else:
            self.errMessage("선택하신 코인은 목록에 없습니다")

    # 사용자 입력 데이터 삭제
    def removeUserData(self):
        for i in self.userSettingData:
            if i['coinName'] in self.cb1.currentText():
                self.userSettingData.remove(i)
        logger.info(self.userSettingData)

    # 매매 코인 목록을 화면에 노출
    def showCoinList(self):
        self.te1.clear()
        for i in self.selectCoinNameList:
            self.te1.append(i)

    # 보유종목 일괄 매도
    def sellAllCoin(self):
        trading_api.sellMyKrwItmList()
        #trading_api.buySelectCoin1()

    # 선택 종목 전액 매도
    def sellSelectCoin(self):
        trading_api.sellSelectCoin(self.cb1.currentText())
        self.repaint()

    # 선택 종목 전액 매수
    def buyAllCoin(self):
        trading_api.buyFullTargetTry(self.cb1.currentText())
        self.repaint()

    # 에러 메세지 노출
    def errMessage(self, message):
        root = Tk()
        root.withdraw()
        msg.showinfo('에러', message)

    # 지정가 매도
    def sellLimitPriceCoin(self):
        trading_api.sellLimitSelectCoin(self.cb1.currentText(), self.qle7.text(), self.qle8.text())
        self.repaint()

    # 지정가 매수
    def buyLimitPriceCoin(self):
        trading_api.buyLimitSelectCoin(self.cb1.currentText(), self.qle7.text(), self.qle8.text())
        self.repaint()

    # 보유종목 분할 매도
    def sellAllShareCoin(self):
        # 사용자 입력 데이터 저장
        self.setUserData()

        # 자동 분할
        #trading_api.sellMyKrwShareItmList()

        # 대기열 갯수 자동 조정
        trading_api.askBidWaitListSort()

    # 파일 저장
    def fileSaveVolume(self):
        # 사용자 입력 데이터 저장
        self.setUserData()

        # 거래항목이 있으면 멉데이트
        trading_api.save_orders_update_to_file(self.cb1.currentText())

        # 무조건 새로 만듬
        # trading_api.save_orders_to_file(self.cb1.currentText())

    # 단타매매 시작
    def startTrading(self):
        # 원화가 많이 남았는치 체크
        #self.checkKrwPrice()

        # 원화가 많이 남았는치 체크 안함
        self.noCheckKrwPrice()


    # 원화가 많이 남았는치 체크
    def checkKrwPrice(self):
        #원화가 많이 남았을때 확인필요(방어로직)
        krwPrice = float(self.qle1.text()) #현재 보유 원화
        divisionPrice = float(self.qle12.text()) #분할 매도 가격

        if(krwPrice > divisionPrice):
            self.errMessage("원화 남은 금액 분할 금액 보다 많습니다")
        else:
            # 사용자 입력 데이터 저장
            self.setUserData()

            if len(self.selectCoinNameList) > 0:
                logger.info("단타매매시작")
                trading_api.isSpeedTradingStartYn = True

                # 현재 원화마켓 보유중인 코인 리스트
                trading_api.myKrwCoinHoldList()

                t = Thread_run(self)
                t.start()
            else:
                self.errMessage("코인을 추가 후 실행 하세요")

    # 원화가 많이 남았는치 체크 안함
    def noCheckKrwPrice(self):
        # 사용자 입력 데이터 저장
        self.setUserData()

        if len(self.selectCoinNameList) > 0:
            logger.info("단타매매시작")
            trading_api.isSpeedTradingStartYn = True

            # 현재 원화마켓 보유중인 코인 리스트
            trading_api.myKrwCoinHoldList()

            t = Thread_run(self)
            t.start()
        else:
            self.errMessage("코인을 추가 후 실행 하세요")

    # 단타매매 종료
    def stopTrading(self):
        logger.info("추세매매종료")
        trading_api.isSpeedTradingStartYn = False

    # 로그 환경을 설정해주는 함수
    def set_logger(self):
        # 로그를 남길 방식 "[로그레벨|라인번호] 날짜 시간,밀리초 > 메시지" 형식 포맷
        # fomatter = logging.Formatter('[%(levelname)s레벨|%(lineno)s라인] %(asctime)s > %(message)s')
        # 로그를 남길 방식 "[로그레벨][파일명:라인번호] 날짜 시간,밀리초 > 메시지" 형식 포맷
        fomatter = logging.Formatter('[%(levelname)s레벨][%(filename)s:%(lineno)d라인] %(asctime)s > %(message)s')

        # 로그 파일 이름 포맷 (YYYYmmdd 형태)
        logday = datetime.today().strftime("%Y%m%d")

        # 파일 최대 용량인 100MB를 변수에 할당 (100MB, 102,400KB)
        fileMaxByte = 1024 * 1024 * 100

        # 파일에 로그를 출력하는 핸들러 (100MB가 넘으면 최대 10개까지 신규 생성)
        fileHandler = logging.handlers.RotatingFileHandler('./LOG_' + str(logday) + '.log', maxBytes=fileMaxByte,
                                                           backupCount=10)
        # 콘솔에 로그를 출력하는 핸들러
        streamHandler = logging.StreamHandler()

        # 파일에 로그를 출력하는 핸들러 포맷
        fileHandler.setFormatter(fomatter)
        # 콘솔에 로그를 출력하는 핸들러 포맷
        streamHandler.setFormatter(fomatter)

        # 로그 인스턴스 파일 로그 출력 핸들러
        logger.addHandler(fileHandler)
        # 로그 인스턴스 콘솔 로그 출력 핸들러
        logger.addHandler(streamHandler)

        # 기본 로그 레벨을 디버그로 만듬
        logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec_())
