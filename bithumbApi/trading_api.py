import datetime
import math
import time
import json
from operator import itemgetter

from requests import get

from bithumbApi import exchange_api
from bithumbApi import quotation_api

logger = None
isSpeedTradingStartYn = False  # 추세매매 시작/ 종료
marketCoinNameObj = []  # 마켓에 등록된 코인 목록
myCoinNameList = []  # 현재 보유 코인 이름 목록
mySelectCoinNameList = []  # 콤보박스 추가된 코인종목 리스트
myTargetPriceList = []  # 코인별 코인별 거래간격,거래수량(%),분할갯수 리스트
myWaitPriceList = []    # 현재 대기중인 매수/매도 리스트
ipAddressFile = ""


# IP 정보로 키값 세팅
def getIpConfig():
    ip_air = "72.14.201.167"
    # ip_air = " 203.227.22.100"

    # ip = get("https://api.ipify.org").text
    # logger.info("My public IP address : " + ip)
    # if ip == ip_air:
    #     fileName = "upbit_home.txt"
    # else:
    #     fileName = "upbit_air.txt"

    return "bithumb_home.txt"


# 업비트 로그인
def login():
    # 로그인 설정
    f = open(ipAddressFile)
    lines = f.read().splitlines()
    access = lines[0]
    secret = lines[1]
    f.close()

    # 로그인
    logins = exchange_api.bithumb(access, secret)

    return logins


# 원화 마켓에 등록된 전체 코인 목록 저장
def getMarketCoins():
    objList = quotation_api.get_tickersObj("KRW")

    for i in objList:
        marketCoinNameObj.append(i)


# 원화 마켓에 등록된 코인 한글 목록 리턴
def getKrwMarketTickers():
    tickers = []
    for i in marketCoinNameObj:
        tickers.append(i['korean_name'])

    return sorted(tickers)


# 현재 원화마켓 보유중인 코인목록 저장
def myKrwCoinHoldList():
    myBalances = login().get_balances()

    myCoinNameList.clear()
    for i in myBalances:
        myCoinNameList.append(i)


# 원화 마켓에 등록된 코인 영문명 리턴
def getEngMarketCoinName(korCoinName):
    for i in marketCoinNameObj:
        if i['korean_name'] == korCoinName:
            return str(i['market'])

    return None


# 현재 보유 중인 원화 가격 리턴
def getKrwTarget():
    # 업비트 현재 원화 전체 금액 가져옴
    krw_balance = login().get_balance("KRW")
    logger.info("****** 현재 보유 원화 리턴 *****")
    logger.info("krw_balance : " + str(krw_balance))

    return krw_balance


# 콤보박스 선택 된 코인의 현재 가격 조회 리턴
def gatCurrentPrice(coinName):
    # 코인명 영문명으로 변환
    krwEngCoinName = getEngMarketCoinName(coinName)

    # 현재 코인 가격
    currentPrice = quotation_api.get_current_price(krwEngCoinName)

    return str(currentPrice)


# 현재 보유 코인 수량 OR 평단가 리턴
def getKrwCoinTarget(coinName, key):
    # 영문 코인명 세팅
    engCoinName = getEngMarketCoinName(coinName)

    # KRW- 문자열 제거
    engCoinName = engCoinName.replace("KRW-", '')

    for i in myCoinNameList:
        if i['currency'] == engCoinName:
            return str(i[key])

    return None


# 사용자 선택(콤보박스) 종목 리스트에 추가
def mySelectCoinList(selectCoinList):
    mySelectCoinNameList.clear()
    for i in selectCoinList:
        mySelectCoinNameList.append(i)
        logger.info(mySelectCoinNameList)


# 보유 코인 판단
def isCoinHoldYn(coinName):
    # 영문 코인명 세팅
    engCoinName = getEngMarketCoinName(coinName)

    # KRW- 문자열 제거
    engCoinName = engCoinName.replace("KRW-", '')

    isUsedYn = False

    # 코인 보유 유무 판단
    for i in myCoinNameList:
        if i['currency'] in engCoinName:
            isUsedYn = True
            break

    return isUsedYn


# 선택 종목 전액 시장가 매수
def buyFullTargetTry(coinName):
    # # 치환 변수
    # appendStr = "000"
    #
    # # 업비트 현재 원화 전체 금액 가져옴
    # krwPrice = str(int(login().get_balance("KRW")))
    #
    # # 현재 문자의 길이
    # strLength = int(len(krwPrice))
    #
    # # 4자리 이상일 경우 뒷자리 000으로 변경
    # if strLength > 3:
    #     krwPrice = krwPrice[0:len(krwPrice) - 3] + appendStr

    # 영문 코인명 세팅
    coinName = getEngMarketCoinName(coinName)

    # 업비트 현재 원화 전체 금액 가져옴
    krw_balance = login().get_balance("KRW")

    # 원화 전체 금액으로 종목 풀 매수
    login().buy_market_order(coinName, krw_balance * 0.99)

    getKrwTarget()


# 선택 종목 시장가 전액 매도
def sellSelectCoin(coinName):
    # 영문 코인명 세팅
    coinName = getEngMarketCoinName(coinName)

    # 영문 코인명으로 매수가격을 가져옴
    btc_balance = login().get_balance(coinName)

    # 코인 전액 매도
    login().sell_market_order(coinName, btc_balance)

    # 원화 업데이트
    getKrwTarget()


# 선택 종목 일괄 매수
def buySelectCoin1():
    logger.info("buySelectCoin CALL !!!")
    for i in myTargetPriceList:
        # 코인명 영문명으로 변환
        krwEngCoinName = getEngMarketCoinName(i['coinName'])

        # 현재 코인 가격
        currentPrice = quotation_api.get_current_price(krwEngCoinName)

        bBuyVolume = 20000.0 / float(currentPrice)

        logger.info("****** 선택 종목 일괄 매수 ******")
        logger.info("매수 코인명 : " + str(i['coinName']))
        logger.info("매수 가격 : " + str(currentPrice))
        logger.info("매수 수량 : " + str(bBuyVolume))
        logger.info("****************************")

        # 지정가 매수
        # login().buy_limit_order(krwEngCoinName, currentPrice, bBuyVolume)


# 보유종목 전체 시장가 전액 매도
def sellMyKrwItmList():
    # 현재 보유 코인 정보
    myBalancers = login().get_balances()

    for i in myBalancers:
        if i['currency'] != 'KRW':
            coinName = "KRW-" + i['currency']
            btc_balance = login().get_balance(coinName)

            # 코인 시장가 매도
            login().sell_market_order(coinName, btc_balance)

            logger.info("****** 시장가 전액 매도 금액 ******")
            logger.info("매도 코인명 : ", coinName)
            logger.info("매도 가격: ", str(btc_balance))
            logger.info("****************************")

    getKrwTarget()


# 콤보박스 선택 종목 분할 매도
def sellMyKrwShareItmList():
    for i in myTargetPriceList:  # 콤보박스 코인 목록
        # 코인명 영문명으로 변환
        krwEngCoinName = getEngMarketCoinName(i['coinName'])

        # 현재 코인 가격
        # currentPrice = quotation_api.get_current_price(krwEngCoinName)
        time.sleep(0.1)  # API 요청시 요청 횟수 제한에 걸려 추가

        # sellPriceRange = get_price_range(currentPrice)
        currentPrice = i['currentPrice']  # 현재 가격
        sellStartPrice = i['sellStartPrice']  # 매도시작가격
        sellSharePrice = i['sellSharePrice']  # 분할매도가격
        sellBalance = i['sellBalance']  # 분할매도수량
        sellMaxCount = i['sellMaxCount']  # 분할 갯수
        sellPriceRange = get_price_range(float(sellStartPrice))

        # for i in range(sellMaxCount, 0, -1):

        for y in range(sellMaxCount * 2, 0, -2):
            limitPrice = round(float(sellStartPrice) + (sellPriceRange * y), 2)
            # limitPrice = currentPrice + (sellPriceRange * (int(sellRange) * y))
            logger.info("****** 분할 매도******")
            logger.info("진 행 회 수 : " + str(y))
            logger.info("매도시작가격 : " + str(sellStartPrice))
            logger.info("분할매도가격 : " + str(sellSharePrice))
            logger.info("매도 호가 : " + str(limitPrice))
            logger.info("매도 수량 : " + str(sellBalance))
            logger.info("****************************")

            # 지정가 매도
            login().sell_limit_order(krwEngCoinName, limitPrice, sellBalance)
            time.sleep(0.2)


# 선택 종목 1호가 단위 리턴
def get_price_range(price):
    if price >= 2000000:
        tick_range = 1000
    elif price >= 1000000:
        tick_range = 500
    elif price >= 500000:
        tick_range = 100
    elif price >= 100000:
        tick_range = 50
    elif price >= 10000:
        tick_range = 10
    elif price >= 1000:
        tick_range = 5
    elif price >= 100:
        tick_range = 1
    elif price >= 10:
        tick_range = 0.1
    else:
        tick_range = 0.01
    return tick_range


# 지정가 매도
def sellLimitSelectCoin(coinName, limitPrice, limitVolume):
    # 영문 코인명 세팅
    engCoinName = getEngMarketCoinName(coinName)

    # 지정가 매도
    login().sell_limit_order(engCoinName, limitPrice, limitVolume)

    logger.info("****** 지정가 매도 ******")
    logger.info("매도 호가 : " + str(limitPrice))
    logger.info("매도 수량 : " + str(limitVolume))
    logger.info("****************************")


# 지정가 매수
def buyLimitSelectCoin(coinName, limitPrice, limitVolume):
    # 영문 코인명 세팅
    engCoinName = getEngMarketCoinName(coinName)

    # 지정가 매수
    login().buy_limit_order(engCoinName, limitPrice, limitVolume)

    logger.info("****** 지정가 매수 ******")
    logger.info("매수 호가 : " + str(limitPrice))
    logger.info("매수 수량 : " + str(limitVolume))
    logger.info("****************************")


# 단타 매매 시작
def speedTradingStart():
    logger.info("speedTradingStart CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(i['coinName'])

            # 현재 코인 가격
            currentPrice = quotation_api.get_current_price(krwEngCoinName)

            sellPriceRange = get_price_range(currentPrice)
            sellRange = i['sellRange']  # 거래간격
            sellShare = i['sellShare']  # 분할갯수
            sellBalance = i['sellBalance']  # 매도갯수(1호가당)

            doneList = login().get_order(krwEngCoinName, "done")
            # doneList = login().get_order("afce08a5-1e65-431c-a05f-0e80db6fbb4b")
            # doneList = sorted(doneList, key=lambda person: (person['price']), reverse=True)

            doneList = isCheckDoneList(doneList)
            bPrice = doneList['price']
            bSide = doneList['side']
            bBuyVolume = float(doneList['volume'])
            bSellVolume = float(doneList['volume'])

            checkRange = float(sellPriceRange) * float(sellRange)
            checkMinPrice = float(currentPrice) - float(checkRange)
            checkMaxPrice = float(currentPrice) + float(checkRange)
            buyPrice = float(bPrice) - float(checkRange)
            sellPrice = float(bPrice) + float(checkRange)

            bBuyVolume = 20000.0 / float(buyPrice)
            bSellVolume = 20000.0 / float(sellPrice)

            if bSide == "bid":  # 매수라면
                # logger.info("매도진입")
                isChek = isCheckWaitList(krwEngCoinName, sellPrice)
                if isChek is False:  # 등록되지않았다면
                    # 지정가 매도
                    login().sell_limit_order(krwEngCoinName, sellPrice, bSellVolume)
                    logger.info("****** 지정가 매도 ******")
                    logger.info("매도 호가 : " + str(sellPrice))
                    logger.info("매도 수량 : " + str(bSellVolume))
                    logger.info("****************************")
            elif bSide == "ask":  # 매도라면
                # logger.info("매수진입")
                isChek = isCheckWaitList(krwEngCoinName, buyPrice)
                # logger.info("isChek : " + str(isChek))
                if isChek is False:  # 등록되지않았다면
                    # 지정가 매수
                    login().buy_limit_order(krwEngCoinName, buyPrice, bBuyVolume)

                    logger.info("****** 지정가 매수 ******")
                    logger.info("매수 호가 : " + str(buyPrice))
                    logger.info("매수 수량 : " + str(bBuyVolume))
                    logger.info("****************************")

            time.sleep(2)


# 단타 매매 시작
def speedTradingStart1():
    logger.info("speedTradingStart CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(i['coinName'])

            # 현재 코인 가격
            currentPrice = float(quotation_api.get_current_price(krwEngCoinName))

            if int(currentPrice) % 2 == 0:
                sellPriceRange = get_price_range(currentPrice)
                sellRange = i['sellRange']  # 거래간격
                # sellShare = i['sellShare']  # 분할갯수
                # sellBalance = i['sellBalance']  # 매도갯수(1호가당)

                checkRange = float(sellPriceRange) * float(sellRange)
                sellPrice = float(currentPrice) + float(checkRange)
                buyPrice = float(currentPrice) - float(checkRange)

                bCurrentVolume = 20000.0 / float(currentPrice)
                bBuyVolume = 100000.0 / float(buyPrice)
                bSellVolume = 100000.0 / float(sellPrice)

                isChek = isCheckWaitList(krwEngCoinName, currentPrice)
                if isChek is False:  # 등록되지않았다면
                    isChek = isCheckWaitList(krwEngCoinName, sellPrice)
                    if isChek is False:  # 등록되지않았다면
                        # 지정가 매도
                        login().sell_limit_order(krwEngCoinName, currentPrice, bCurrentVolume)
                        login().sell_limit_order(krwEngCoinName, sellPrice, bSellVolume)
                        logger.info("****** 지정가 매도 ******")
                        logger.info("매도 호가 : " + str(sellPrice))
                        logger.info("매도 수량 : " + str(bSellVolume))
                        logger.info("****************************")

                    else:
                        isChek = isCheckWaitList(krwEngCoinName, buyPrice)
                        if isChek is False:  # 등록되지않았다면
                            logger.info("현재가격 1: " + str(currentPrice))

                            # 지정가 매수
                            login().buy_limit_order(krwEngCoinName, currentPrice, bCurrentVolume)
                        login().buy_limit_order(krwEngCoinName, buyPrice, bBuyVolume)

                        logger.info("****** 지정가 매수 ******")
                        logger.info("매수 호가 : " + str(currentPrice))
                        logger.info("매수 수량 : " + str(bBuyVolume))
                        logger.info("****************************")

            time.sleep(2)


# 단타 매매 시작
def speedTradingStart3():
    logger.info("speedTradingStart3 CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(i['coinName'])

            # 현재 코인 가격
            currentPrice = quotation_api.get_current_price(krwEngCoinName)

            sellPriceRange = get_price_range(currentPrice)
            sellRange = i['sellRange']  # 거래간격
            # logger.info("****** 거래간격 ******")
            # logger.info("sellPriceRange : " + str(sellPriceRange))
            # logger.info("sellRange: " + str(sellRange))
            # logger.info("****************************")

            checkRange = float(sellPriceRange) * float(sellRange)
            buyPrice = round(float(currentPrice) - float(checkRange), 2)
            sellPrice = round(float(currentPrice) + float(checkRange), 2)
            # logger.info("****** 매도/매수 가격 ******")
            # logger.info("현재 가격 : " + str(currentPrice))
            # logger.info("매도 가격: " + str(sellPrice))
            # logger.info("****************************")

            bBuyVolume = 100000.0 / float(currentPrice)
            # bBuyVolume = 100000.0 / float(currentPrice)
            # bSellVolume = 20000.0 / float(sellPrice)

            # doneList = login().get_order(krwEngCoinName, "done")
            # waitList = isCheckWaitList(krwEngCoinName, sellPrice)
            # logger.info("****** 호출 시작 ******")
            # logger.info("currentPrice : " + str(currentPrice))
            isCWaitListFlag = isCheckWaitList(krwEngCoinName, currentPrice)
            # logger.info("isCWaitListFlag : " + str(isCWaitListFlag))
            # isCdoneListFlag = isUseDoneList(krwEngCoinName, currentPrice)
            # logger.info("isDoneListFlag : " + str(isCdoneListFlag))
            isSWaitListFlag = isCheckWaitList(krwEngCoinName, sellPrice)
            # logger.info("isSWaitListFlag : " + str(isSWaitListFlag))
            if isCWaitListFlag is False and isSWaitListFlag is False:  # 등록되지않았다면
                # 지정가 매수
                login().buy_limit_order(krwEngCoinName, currentPrice, bBuyVolume)
                logger.info("****** 지정가 매수 ******")
                logger.info("매수 호가 : " + str(currentPrice))
                logger.info("매수 수량 : " + str(bBuyVolume))
                logger.info("****************************")

                time.sleep(1);
                # 지정가 매도
                login().sell_limit_order(krwEngCoinName, sellPrice, bBuyVolume)
                logger.info("****** 지정가 매도 ******")
                logger.info("매도 호가 : " + str(sellPrice))
                logger.info("매도 수량 : " + str(bBuyVolume))
                logger.info("****************************")

            # isSWaitListFlag = isCheckWaitList(krwEngCoinName, sellPrice)
            # logger.info("isWaitListFlag : " + str(isSWaitListFlag))
            # if isSWaitListFlag is False: # 등록되지않았다면
            #     # 지정가 매도
            #     #login().sell_limit_order(krwEngCoinName, sellPrice, bBuyVolume)
            #     logger.info("****** 지정가 매도 ******")
            #     logger.info("매도 호가 : " + str(sellPrice))
            #     logger.info("매도 수량 : " + str(bBuyVolume))
            #     logger.info("****************************")

            time.sleep(19)


# 단타 매매 시작
def speedTradingStart4():
    logger.info("speedTradingStart4 CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(i['coinName'])
            sellStartPrice = i['sellStartPrice']  # 매도시작가격
            sellPriceRange = get_price_range(float(sellStartPrice))

            # 현재 코인 가격
            currentPrice = quotation_api.get_current_price(krwEngCoinName)
            isCWaitListFlag = isCheckWaitList(krwEngCoinName, currentPrice)

            sellRange = i['sellRange']  # 거래간격
            checkRange = float(sellPriceRange) * float(sellRange)
            sellPrice = round(float(currentPrice) + float(checkRange), 2)
            isSWaitListFlag = isCheckWaitList(krwEngCoinName, sellPrice)

            sellBalance = i['sellBalance']  # 분할매도수량

            if isCWaitListFlag is False and isSWaitListFlag is False:  # 등록되지않았다면
                # 지정가 매수
                login().buy_limit_order(krwEngCoinName, currentPrice, sellBalance)
                logger.info("****** 지정가 매수 ******")
                logger.info("매수 호가 : " + str(currentPrice))
                logger.info("매수 수량 : " + str(sellBalance))
                logger.info("****************************")

                time.sleep(1);
                # 지정가 매도
                login().sell_limit_order(krwEngCoinName, sellPrice, sellBalance)
                logger.info("****** 지정가 매도 ******")
                logger.info("매도 호가 : " + str(sellPrice))
                logger.info("매도 수량 : " + str(sellBalance))
                logger.info("****************************")

            time.sleep(9)


# 단타 매매 시작
def speedTradingStart5():
    logger.info("speedTradingStart5 CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(i['coinName'])

            # 현재 코인 가격
            currentPrice = quotation_api.get_current_price(krwEngCoinName)
            strCurrentPrice = str(currentPrice)
            lastString = strCurrentPrice[-1:]

            sellMaxCount = 11;
            sellPriceRange = get_price_range(float(currentPrice))
            sellBalance = i['sellBalance']  # 분할매도수량

            if lastString != '5':
                for y in range(sellMaxCount, 0, -1):
                    checkRange = sellPriceRange * y
                    sellPrice = round(currentPrice + checkRange, 2)
                    isCWaitListFlag = isCheckWaitList(krwEngCoinName, sellPrice)

                    if (isCWaitListFlag is False):  # 등록되지않았다면
                        # 지정가 매수
                        # login().buy_limit_order(krwEngCoinName, sellPrice, sellBalance)
                        logger.info("****** 지정가 매수 ******")
                        logger.info("매수 호가 : " + str(sellPrice))
                        logger.info("매수 수량 : " + str(sellBalance))
                        logger.info("****************************")

                        time.sleep(1);

            time.sleep(9);


# 세이  1개종목 10호가 매매
def speedTradingStart6():
    logger.info("speedTradingStart6 CALL !!!")
    while isSpeedTradingStartYn:
        for i in myTargetPriceList:

            korCoinName = i['coinName']
            # 코인명 영문명으로 변환
            krwEngCoinName = getEngMarketCoinName(korCoinName)

            # 업비트 현재 매도 가능한 수량 리턴
            btc_balance = login().get_balance(krwEngCoinName)

            # 현재 코인 가격
            currentPrice = quotation_api.get_current_price(krwEngCoinName)
            # logger.info("******* 10초 주기 실행 *******")
            # logger.info("현재가격 : " + str(currentPrice))
            # logger.info("****************************")

            # 현재 코인 가격 기준 원화 가격으로 변환
            krw_price = float(btc_balance) * float(currentPrice)

            sellRange = int(i['sellRange'])  # 거래간격
            sellShare = int(i['sellSharePrice'])  # 분할갯수

            if 20008 <= krw_price <= 2000000 :  # 매도 가능 금액이 2만원 보다 크고 20만원보다 작으면
                logger.info("====== 매도 가능 금액 ======")
                logger.info("매도금액 : " + str(krw_price))
                logger.info("==========================")

                # 반복할 카운트 횟수
                sellCount = math.trunc(krw_price / sellShare)

                # 대기 리스트 업데이트
                setWaitPriceList(korCoinName)

                # 현재 대기중인 매도 리스트 에서 제일 낮은 가격 리턴
                minAskPrice = getAskBidWaitListPrice(krwEngCoinName, False, str('ask'))

                if minAskPrice > 0:

                    for i in range(sellCount):
                        sellPrice = minAskPrice - i - 1
                        # bSellVolume = round(20000 / (sellPrice-1), 8)

                        time.sleep(1)
                        factor = 10 ** 8
                        # 3만원 이하면 전액 매도
                        if sellShare <= krw_price <= 30000:
                            #krw_price = math.floor((krw_price + 50) * factor) / factor
                            #bSellVolume = math.floor((krw_price / sellPrice) * factor) / factor
                            bSellVolume = btc_balance
                            logger.info("3만원 미만 매도 수량 : " + str(bSellVolume))
                        else:
                            #bSellVolume = math.floor((sellShare / sellPrice) * factor) / factor
                            logger.info("sellCount : " + str(sellCount))
                            if sellCount > 1:
                                bSellVolume = math.floor((btc_balance / sellCount) * factor) / factor

                        isSWaitListFlag = isCheckWaitList(krwEngCoinName, float(sellPrice - sellRange))
                        if isSWaitListFlag is False:  # 등록되지않았다면
                            if bSellVolume > 1:
                                # 지정가 매도
                                login().sell_limit_order(krwEngCoinName, sellPrice, bSellVolume)

                                logger.info("****** 지정가 매도 ******")
                                logger.info("매도 호가 : " + str(sellPrice))
                                logger.info("매도 수량 : " + str(bSellVolume))
                                logger.info("****************************")

            # 업비트 현재 남아 있는 원화 전체 금액 가져 옴
            krw_balance =  math.floor(login().get_balance("KRW"))

            if 20008 <= krw_balance <= 2000000:  # 매도 가능 금액이 2만원 보다 크고 20만원보다 작으면
                logger.info("===== 전체 매수 가능 금액 =====")
                logger.info("원화금액 : " + str(krw_balance))
                logger.info("============================")

                # 반복할 카운트 횟수
                buyCount = math.trunc(krw_balance / sellShare)

                # 대기 리스트 업데이트
                setWaitPriceList(korCoinName)

                # 현재 대기중인 매수 리스트 에서 제일 높은 가격 리턴
                minBidPrice = getAskBidWaitListPrice(krwEngCoinName, True, str('bid'))

                if minBidPrice > 0:

                    for i in range(buyCount):
                        buyPrice = minBidPrice + i + 1
                        # bBuyVolume = round(20000 / buyPrice, 8)

                        time.sleep(1)
                        factor = 10 ** 8
                        # 3만원 이하면 전액 매수
                        if sellShare <= krw_balance <= 30000:
                            krw_balance = krw_balance * 0.9974
                            bBuyVolume = math.floor((krw_balance / buyPrice) * factor) / factor
                            logger.info("3만원 미만 매수 수량 : " + str(bBuyVolume))
                        else:
                            #bBuyVolume = math.floor((sellShare / buyPrice) * factor) / factor
                            if buyCount > 1:
                                krw_balance1 = (krw_balance * 0.9974) / buyCount
                                logger.info("1호가 가격 : " + str(krw_balance1))
                                bBuyVolume = math.floor((krw_balance1 / buyPrice) * factor) / factor

                        isSWaitListFlag = isCheckWaitList(krwEngCoinName, float(buyPrice + sellRange))
                        if isSWaitListFlag is False:  # 등록되지않았다면
                            if bBuyVolume > 1:
                                # 지정가 매수
                                login().buy_limit_order(krwEngCoinName, buyPrice, bBuyVolume)

                                logger.info("****** 지정가 매수 ******")
                                logger.info("매수 호가 : " + str(buyPrice))
                                logger.info("매수 수량 : " + str(bBuyVolume))
                                logger.info("****************************")

            time.sleep(10)

# 현재 대기중인 매수/매도 목록 체크
def isCheckDoneList(doneList):
    afterUuidList = []
    for index, val in enumerate(doneList):
        if index == 0:
            uuidList = login().get_order(val['uuid'])
            tempList = uuidList['trades']
            afterUuidList = tempList[0]
        else:
            uuidList = login().get_order(val['uuid'])
            tempList = uuidList['trades']
            tempList = tempList[0]
            strDate = str(tempList['created_at'])
            strDate = changeDateTime(strDate)

            strDate1 = str(afterUuidList['created_at'])
            strDate1 = changeDateTime(strDate1)

            if strDate1 <= strDate:
                afterUuidList = tempList

    return afterUuidList


def changeDateTime(strTime):
    datetime_str = ""
    datetime_str += str(strTime[0:10])
    datetime_str += " " + str(strTime[11:19])
    data_time_obj = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    return data_time_obj

# 현재 대기중인 매도/매수 리스트 세팅
def setWaitPriceList(coinName):
    global myWaitPriceList  # 글로벌 변수 사용을 선언
    if myWaitPriceList:
        myWaitPriceList.clear()

    # 영문 코인명 세팅
    engCoinName = getEngMarketCoinName(coinName)

    # 대기중인 주문 목록 가져오기
    myWaitPriceList = login().get_order(engCoinName, "wait", "watch", '100')


# 현재 대기중인 매도/매수 리스트 에서 MIN 가격 리턴
def getAskBidWaitListPrice(krwEngCoinName, flag, type):
    #waitList = login().get_order(krwEngCoinName, "wait", "watch", '100')

    waitList = sorted(myWaitPriceList, reverse=flag, key=lambda price: price["price"])

    if type == str('bid'):
        checkList = [item for item in waitList if str(item['side']) == ('ask')]
        logger.info('ASK LIST SIZE : ' + str(len(checkList)))
        if len(checkList) <= 0:
            return 0
    elif type == str('ask'):
        checkList = [item for item in waitList if str(item['side']) == ('bid')]
        logger.info('BID LIST SIZE : ' + str(len(checkList)))
        if len(checkList) <= 0:
            return 0

    for i in waitList:
        # logger.info("거래대기리스트 : " + str(i['price']))
        if str(i['side']) == type:
            return float(i['price'])

    return 0


# 현재 대기중인 매수/매도 목록 체크
def isCheckWaitList(krwEngCoinName, checkPrice):
    #waitList = login().get_order(krwEngCoinName, "wait", "watch", '100')

    for i in myWaitPriceList:
        # logger.info("거래대기리스트 : " + str(i['price']))
        if float(i['price']) == float(checkPrice):
            return True

    return False

# 거래완료 리스목록에서 포함 유무
def isUseDoneList(krwEngCoinName, checkPrice):
    doneList = login().get_order(krwEngCoinName, "done", "watch", '3')

    for i in doneList:
        logger.info("거래완료리스트 : " + str(i['price']))
        if float(i['price']) == float(checkPrice):
            return True

    return False

# 현재 대기중인 매도/매수 리스트에서 대기열 갯수 자동 조정
def askBidWaitListSort():
    for i in myTargetPriceList:  # 콤보박스 코인 목록
        # 코인명 영문명으로 변환
        krwEngCoinName = getEngMarketCoinName(i['coinName'])

        sellSharePrice = int(i['sellSharePrice'])  # 분할매도가격

        # 대기 리스트 조회
        waitPriceList = login().get_order(krwEngCoinName, "wait", "watch", '100')

        # 거래대기리스트를 가격 기준 낮은가격이 위로 정렬
        waitCancelList = sorted(waitPriceList, reverse=False, key=lambda price: price["price"])
        # 매수리스트 주문취소 (낮은금액첫번째아이템삭제)
        login().cancel_order(str(waitCancelList[0]['uuid']))
        time.sleep(1)
        waitCancelList.pop(0)

        # 매수만 필터링
        cancelList = [item for item in waitCancelList if str(item['side']) == ('bid')]
        bidLastPrice=cancelList[0]['price']

        # 거래대기리스트를 가격 기준 높은가격이 위로 정렬
        waitBuylList = sorted(waitPriceList, reverse=True, key=lambda price: price["price"])
        # 매도리스트 주문취소 (높은금액첫번째아이템삭제)
        login().cancel_order(str(waitBuylList[0]['uuid']))
        time.sleep(1)
        waitBuylList.pop(0)

        # 매도만 필터링
        buyList = [item for item in waitBuylList if str(item['side']) == 'ask']
        askLastPrice=buyList[0]['price']

        # 파일에서 기존 데이터 읽기
        existing_orders = read_orders_from_file()

        logger.info('total SIZE: ' + str(len(cancelList)))
        # 매수리스트가 50개보다 클  경우
        if len(cancelList) > 50:
            logger.info('매수리스트 갯수 : ' + str(len(cancelList)))
            gap = len(cancelList) - 50

            for i in range(gap):
                #마지막이면
                if i == gap - 1:
                    # 업비트 현재 매도 가능한 수량 리턴
                    btc_balance = login().get_balance(krwEngCoinName)

                    # 매수리스트 주문취소
                    login().cancel_order(str(cancelList[i]['uuid']))

                    # 지정가 매도
                    login().sell_limit_order(krwEngCoinName, 700, btc_balance)
                else:
                    logger.info(str(cancelList[i]['price']))
                    logger.info(str(cancelList[i]['uuid']))
                    logger.info('매수리스트가 50개보다 큼 주문취소')

                    # 매수리스트 주문취소 (낮은금액부터삭제)
                    login().cancel_order(str(cancelList[i]['uuid']))
                    time.sleep(1)

        # 매수리스트가 50개보다 작을 경우
        elif len(cancelList) < 50:
            logger.info('매수리스트 갯수 : ' + str(len(cancelList)))
            gap = 50 - len(cancelList)

            logger.info('GAP : ' + str(gap))
            for i in range(gap):
                if i == gap - 1:
                    # 업비트 현재 남아 있는 원화 전체 금액 가져 옴
                    krw_balance = login().get_balance("KRW")

                    krw_balance = krw_balance * 0.9974  # 수수료 0.05% 고려
                    factor = 10 ** 8
                    bBuyVolume = math.floor((krw_balance / 100) * factor) / factor
                    logger.info("전체 매수 수량 : " + str(bBuyVolume))

                    # 지정가 매수
                    login().buy_limit_order(krwEngCoinName, 100, bBuyVolume)
                else:
                    buyPrice = int(bidLastPrice) - i - 1
                    factor = 10 ** 8
                    bBuyVolume = math.floor((sellSharePrice / buyPrice) * factor) / factor

                    # volume 값 검색
                    volume = get_volume_by_price_in_updated_orders(existing_orders, buyPrice, target_type='bid')
                    if volume is not None:
                        bBuyVolume = volume
                        logger.info("매수 수량 변경 : " + str(bBuyVolume))

                    logger.info(str(buyPrice))
                    logger.info(str(bBuyVolume))
                    logger.info('매수리스트가 50개보다 작음 지정가 매수')

                    # 지정가 매수
                    login().buy_limit_order(krwEngCoinName, buyPrice, bBuyVolume)
                    time.sleep(1)

        # 매도리스트가 48개보다 클 경우
        if len(buyList) > 48:
            logger.info('매도리스트 갯수 : ' + str(len(buyList)))
            gap = len(buyList) - 48

            for i in range(gap):
                #마지막이면
                if i == gap - 1:
                    # 업비트 현재 매도 가능한 수량 리턴
                    btc_balance = login().get_balance(krwEngCoinName)

                    # 매수리스트 주문취소
                    login().cancel_order(str(waitBuylList[i]['uuid']))

                    # 지정가 매도
                    login().sell_limit_order(krwEngCoinName, 700, btc_balance)
                    logger.info("전체 매도 수량 : " + str(btc_balance))
                else:
                    logger.info(str(waitBuylList[i]['price']))
                    logger.info(str(waitBuylList[i]['uuid']))
                    logger.info('매도리스트가 48개보다 큼 높은가격부터 취소')

                    # 매도리스트 주문취소 (높믄가격부터 취소)
                    login().cancel_order(str(waitBuylList[i]['uuid']))
                    time.sleep(1)

        # 매도리스트가 48개보다 작을 경우
        elif len(buyList) < 48:
            logger.info('매도리스트 갯수 : ' + str(len(buyList)))
            gap = 48 - len(buyList)

            logger.info('GAP : ' + str(gap))
            for i in range(gap):
                if i == gap - 1:
                    # 업비트 현재 매도 가능한 수량 리턴
                    btc_balance = login().get_balance(krwEngCoinName)

                    # 지정가 전체매도
                    login().sell_limit_order(krwEngCoinName, 700, btc_balance)
                    logger.info("전체 매도 수량 : " + str(btc_balance))
                else:
                    sellPrice = int(askLastPrice) + i + 1
                    factor = 10 ** 8
                    bSellVolume = math.floor((sellSharePrice / (sellPrice - 2)) * factor) / factor

                    # volume 값 검색
                    volume = get_volume_by_price_in_updated_orders(existing_orders, sellPrice, target_type='ask')
                    if volume is not None:
                        bSellVolume = volume
                        logger.info("매도 수량 변경 : " + str(bSellVolume))

                    logger.info(str(sellPrice))
                    logger.info(str(bSellVolume))
                    logger.info('매도리스트가 48개보다 작음 지정가 매도')

                    # 지정가 매도
                    login().sell_limit_order(krwEngCoinName, sellPrice, bSellVolume)
                    time.sleep(1)

# 주문 대기 리스트 파일로 저장
def save_orders_to_file(korCoinName):
    filename = 'completed_orders.json'

    # 코인명 영문명으로 변환
    krwEngCoinName = getEngMarketCoinName(korCoinName)

    # 대기중인 주문 목록 가져오기
    orders = login().get_order(krwEngCoinName, "wait", "watch", '100')

    # 거래대기리스트를 가격 기준 높은가격이 위로 정렬
    sortdata = sorted(orders, reverse=True, key=lambda price: price["price"])

    if sortdata:
        with open(filename, 'w') as f:
            json.dump(sortdata, f, indent=4)
        logger.info('주문 대기 리스트 저장')
    else:
        logger.info('주문 대기 리스트가 비어있음')

# 주문 대기 리스트 비교하여 업데이트 파일로 저장
def save_orders_update_to_file(korCoinName):
    # 파일에서 기존 데이터 읽기
    existing_orders = read_orders_from_file()

    # 대기 리스트 업데이트
    setWaitPriceList(korCoinName)

    # 데이터 비교 및 업데이트
    updated_orders = update_data(existing_orders, myWaitPriceList)

    # 업데이트된 데이터를 파일에 저장
    save_to_json_file(updated_orders)

# 저장된 JSON 파일을 읽는 함수
def read_orders_from_file():
    filename = 'completed_orders.json'

    try:
        with open(filename, 'r') as f:
            orders = json.load(f)
        logger.info('성공 대기리스트 읽음')
        return orders
    except FileNotFoundError:
        logger.info('실패 대기리스트 존재하 않음 빈값 반환')
        return []
    except json.JSONDecodeError:
        logger.info('오류 파일 형식이 JSON 형식이 아님 빈값 반환')
        return []

# 데이터 업데이트 함수
def update_data(existing_data, new_data):
    updated_data = existing_data.copy()
    prices_and_sides = {(item['price'], item['side']) for item in updated_data}  # 기존 데이터의 (price, side) 집합

    for item in new_data:
        if (item['price'], item['side']) in prices_and_sides:
            # 동일한 price와 side가 있는 경우 기존 데이터 교체
            updated_data = [
                i if not (i['price'] == item['price'] and i['side'] == item['side']) else item
                for i in updated_data
            ]
            # 가격과 side가 동일한 항목을 교체했을 때 로그 찍기
            #logger.info(f'기존 데이터의 price {item["price"]}와 side {item["side"]}가 교체되었습니다.')
        else:
            # 새로운 price와 side 추가
            updated_data.append(item)
            logger.info('새로운 price와 side 추가 : ' + item['price'])

    return updated_data

# JSON 파일 저장 함수
def save_to_json_file(data):
    filename = 'completed_orders.json'

    # 거래대기리스트를 가격 기준 높은가격이 위로 정렬
    sortdata = sorted(data, reverse=True, key=lambda price: price["price"])

    try:
        with open(filename, 'w') as file:
            json.dump(sortdata, file, indent=4)
        logger.info('파일 저장 성공')
    except Exception as e:
        logger.info('파일 저장 중 오류 발생')


# 특정 price에 대한 volume 검색 함수
def get_volume_by_price_in_updated_orders(updated_orders, target_price, target_type):
    """
    updated_orders에서 target_price에 해당하는 volume 값을 반환합니다.
    """
    for order in updated_orders:
        if (float(order.get('price')) == float(target_price) and
                order.get('side') == str(target_type)):  # price와 type을 비교
            volume = order.get('volume')
            logger.info("변경된 수량 : " + str(volume))
            return order.get('volume')  # volume 값 반환

    # 값이 없을 경우 None 반환
    return None