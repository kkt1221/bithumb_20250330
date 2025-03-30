import jwt          # PyJWT
import json
import re
import uuid
import time
import hashlib
from urllib.parse import urlencode

import requests

from bithumbApi.request_api import _send_get_request, _send_post_request, _send_delete_request

logger = None

# 원화 마켓 주문 가격 단위
# https://docs.upbit.com/docs/market-info-trade-price-detail
def get_tick_size(price):
    if price >= 2000000:
        tick_size = round(price / 1000) * 1000
    elif price >= 1000000:
        tick_size = round(price / 500) * 500
    elif price >= 500000:
        tick_size = round(price / 100) * 100
    elif price >= 100000:
        tick_size = round(price / 50) * 50
    elif price >= 10000:
        tick_size = round(price / 10) * 10
    elif price >= 1000:
        tick_size = round(price / 5) * 5
    elif price >= 100:
        tick_size = round(price / 1) * 1
    elif price >= 10:
        tick_size = round(price / 0.1) / 10
    else:
        tick_size = round(price / 0.01) / 100
    return tick_size


class bithumb:
    def __init__(self, access, secret):
        self.access = access
        self.secret = secret

    def _request_headers(self, requestBody=None):

        if requestBody is not None:
            query = urlencode(requestBody).encode()
            hash = hashlib.sha512()
            hash.update(query)
            query_hash = hash.hexdigest()
            payload = {
             'access_key': self.access,
             'nonce': str(uuid.uuid4()),
             'timestamp': round(time.time() * 1000),
             'query_hash': query_hash,
             'query_hash_alg': 'SHA512',
            }
        else:
            payload = {
             "access_key": self.access,
             "nonce": str(uuid.uuid4()),
             'timestamp': round(time.time() * 1000),
            }

        # if query is not None:
        #     m = hashlib.sha512()
        #     m.update(urlencode(query).encode(), algorithm="HS256")
        #     query_hash = m.hexdigest()
        #     payload['query_hash'] = query_hash
        #     payload['query_hash_alg'] = "SHA512"

        #jwt_token = jwt.encode(payload, self.secret, algorithm="HS256").decode('utf-8')
        jwt_token = jwt.encode(payload, self.secret)     # PyJWT >= 2.0
        authorization_token = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization_token,
            'Content-Type': 'application/json'
        }
        return headers

    def get_myBalance(self, ticker="KRW", contain_req=False):
        """
        특정 코인/원화의 잔고를 조회하는 메소드
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 제외)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # fiat-ticker
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            # search the current currency
            balance = []
            for x in balances:
                balance.append(x['currency'])

            return balance
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(balances)
            return None

    # region balance
    def get_balances(self, contain_req=False):
        """
        전체 계좌 조회
        :param contain_req: Remaining-Req 포함여부
        :return: 내가 보유한 자산 리스트
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            url = "https://api.bithumb.com/v1/accounts"
            headers = self._request_headers()
            result = _send_get_request(url, headers=headers)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def get_balance(self, ticker="KRW", contain_req=False):
        """
        특정 코인/원화의 잔고를 조회하는 메소드
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 제외)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        retry_attempt = 0  # 재시도 횟수
        max_retries = 1  # 최대 재시도 횟수
        while retry_attempt <= max_retries:

            try:
                # fiat-ticker
                # KRW-BTC
                if '-' in ticker:
                    ticker = ticker.split('-')[1]

                balances, req = self.get_balances(contain_req=True)

                # search the current currency
                balance = 0
                for x in balances:
                    if x['currency'] == ticker:
                        balance = float(x['balance'])
                        break

                if contain_req:
                    return balance, req
                else:
                    return balance
            except Exception as x:
                if retry_attempt < max_retries:
                    retry_attempt += 1
                    print(f"get_balance Request failed. Retrying {retry_attempt}/{max_retries}...")
                    time.sleep(3)  # 재시도 전 대기 시간 (필요시 조정 가능)
                else:
                    print(x.__class__.__name__)
                    logger.info(balances)
                    return None

    def get_balance_t(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 잔고 조회(balance + locked)
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 주문가능 금액/수량 (주문 중 묶여있는 금액/수량 포함)
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            balance = 0
            locked = 0
            for x in balances:
                if x['currency'] == ticker:
                    balance = float(x['balance'])
                    locked = float(x['locked'])
                    break

            if contain_req:
                return balance + locked, req
            else:
                return balance + locked
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(balances)
            return None

    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 매수평균가 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 매수평균가
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            avg_buy_price = 0
            for x in balances:
                if x['currency'] == ticker:
                    avg_buy_price = float(x['avg_buy_price'])
                    break
            if contain_req:
                return avg_buy_price, req
            else:
                return avg_buy_price

        except Exception as x:
            print(x.__class__.__name__)
            logger.info(balances)
            return None

    def get_amount(self, ticker, contain_req=False):
        """
        특정 코인/원화의 매수금액 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드 (ALL 입력시 총 매수금액 조회)
        :param contain_req: Remaining-Req 포함여부
        :return: 매수금액
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            amount = 0
            for x in balances:
                if x['currency'] == 'KRW':
                    continue

                avg_buy_price = float(x['avg_buy_price'])
                balance = float(x['balance'])
                locked = float(x['locked'])

                if ticker == 'ALL':
                    amount += avg_buy_price * (balance + locked)
                elif x['currency'] == ticker:
                    amount = avg_buy_price * (balance + locked)
                    break
            if contain_req:
                return amount, req
            else:
                return amount
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(balances)
            return None

    # endregion balance

    # region chance
    def get_chance(self, ticker, contain_req=False):
        """
        마켓별 주문 가능 정보를 확인.
        :param ticker:
        :param contain_req: Remaining-Req 포함여부
        :return: 마켓별 주문 가능 정보를 확인
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
        try:
            url = "https://api.bithumb.com/v1/orders/chance"
            data = {"market": ticker}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    # endregion chance

    # region order
    def buy_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매수
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        attempt = 0  # 시도 횟수 카운터
        max_retries = 1  # 재시도 횟수 설정 (예외 발생 시 1번 재시도)

        while attempt <= max_retries:
            try:
                url = "https://api.bithumb.com/v1/orders"
                # data = {"market": ticker,
                #         "side": "bid",
                #         "volume": str(volume),
                #         "price": str(price),
                #         "ord_type": "limit"}
                # headers = self._request_headers(data)
                # result = _send_post_request(url, headers=headers, data=data)
                requestBody = dict(market=ticker, ord_type='limit', price=str(price), side='bid', volume=str(volume))
                headers = self._request_headers(requestBody)
                result = _send_post_request(url, data=json.dumps(requestBody), headers=headers)

                if contain_req:
                    return result
                else:
                    return result[0]
            except Exception as x:
                time.sleep(3)
                attempt += 1
                logger.info(result)

                if attempt > max_retries:
                    print(x.__class__.__name__)
                    logger.info(result)
                    return None

    def buy_market_order(self, ticker, price, contain_req=False):
        """
        시장가 매수
        :param ticker: ticker for cryptocurrency
        :param price: KRW
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/orders"
            data = {"market": ticker,  # market ID
                    "side": "bid",  # buy
                    "price": str(price),
                    "ord_type": "price"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def sell_market_order(self, ticker, volume, contain_req=False):
        """
        시장가 매도 메서드
        :param ticker: 가상화폐 티커
        :param volume: 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/orders"
            data = {"market": ticker,  # ticker
                    "side": "ask",  # sell
                    "volume": str(volume),
                    "ord_type": "market"}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def sell_limit_order(self, ticker, price, volume, contain_req=False):
        """
        지정가 매도
        :param ticker: 마켓 티커
        :param price: 주문 가격
        :param volume: 주문 수량
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        attempt = 0  # 시도 횟수 카운터
        max_retries = 1  # 재시도 횟수 설정 (예외 발생 시 1번 재시도)

        while attempt <= max_retries:
            try:
                url = "https://api.bithumb.com/v1/orders"
                # data = {"market": ticker,
                #         "side": "ask",
                #         "volume": str(volume),
                #         "price": str(price),
                #         "ord_type": "limit"}
                requestBody = dict(market=ticker, ord_type='limit', price=str(price), side='ask', volume=str(volume))
                headers = self._request_headers(requestBody)

                result = _send_post_request(url, data=json.dumps(requestBody), headers=headers)

                if contain_req:
                    return result
                else:
                    return result[0]
            except Exception as x:
                time.sleep(3)
                attempt += 1
                logger.info(result)

                if attempt > max_retries:
                    print(x.__class__.__name__)
                    logger.info(result)
                    return None

    def cancel_order(self, uuid1, contain_req=False):
        """
        주문 취소
        :param uuid: 주문 함수의 리턴 값중 uuid
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/order"
            #data = {"uuid": 'C0565000000359323097'}
            #data = dict(uuid='C0565000000359323097')
            #headers = self._request_headers(data)
            #result = _send_delete_request(url, headers=headers, data=data)
            # Set API parameters
            data = dict(uuid=uuid1)

            # Generate access token
            query = urlencode(data).encode()
            hash = hashlib.sha512()
            hash.update(query)
            query_hash = hash.hexdigest()
            payload = {
                'access_key': self.access,
                'nonce': str(uuid.uuid4()),
                'timestamp': round(time.time() * 1000),
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512',
            }
            jwt_token = jwt.encode(payload, self.secret)
            authorization_token = 'Bearer {}'.format(jwt_token)
            headers = {
                'Authorization': authorization_token
            }
            # result = _send_delete_request(url, headers=headers, data=data)
            result = requests.delete(url, params=data, headers=headers)
            #result = _send_delete_request(url, headers=headers, data=data)

            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def get_order(self, ticker_or_uuid, state='wait', kind='watch', limit='100', contain_req=False):
        """
        주문 리스트 조회
        :param ticker: market
        :param state: 주문 상태(wait, done, cancel)
        :param kind: 주문 유형(normal, watch)
        :param limit: 요청개수, default =100
        :param contain_req: Remaining-Req 포함여부
        :return:
        """

        attempt = 0
        max_retries = 1

        while attempt <= max_retries:

            # TODO : states, identifiers 관련 기능 추가 필요
            try:
                p = re.compile(r"^\w+-\w+-\w+-\w+-\w+$")
                # 정확히는 입력을 대문자로 변환 후 다음 정규식을 적용해야 함
                # - r"^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$"
                is_uuid = len(p.findall(ticker_or_uuid)) > 0
                if is_uuid:
                    url = "https://api.bithumb.com/v1/order"
                    data = {'uuid': ticker_or_uuid}
                    headers = self._request_headers(data)
                    result = _send_get_request(url, headers=headers, data=data)
                else :
                    url = "https://api.bithumb.com/v1/orders"
                    # data = {'market': ticker_or_uuid,
                    #         'state': state,
                    #         'kind': kind,
                    #         'limit': limit,
                    #         'order_by': 'desc'
                    #         }
                    try:
                        headers = self._request_headers()
                        param = dict(market=ticker_or_uuid, state=state, kind=kind, limit=limit, page=1, order_by='desc')
                        query = urlencode(param)
                        result = _send_get_request(url, headers=headers, data=query)
                    except requests.ConnectionError as e:
                        logger.error(f"ConnectionError occurred: {e}")
                        time.sleep(3)
                        attempt += 1
                        if attempt > max_retries:
                            logger.error("Max retries reached. Unable to connect.")
                            return None

                if contain_req:
                    return result
                else:
                    return result[0]
            except Exception as x:
                time.sleep(3)
                attempt += 1
                logger.info(result)

                if attempt > max_retries:
                    print(x.__class__.__name__)
                    logger.info(result)
                    return None

    def get_individual_order(self, uuid, contain_req=False):
        """
        주문 리스트 조회
        :param uuid: 주문 id
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        # TODO : states, uuids, identifiers 관련 기능 추가 필요
        try:
            url = "https://api.bithumb.com/v1/order"
            data = {'uuid': uuid}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None
    # endregion order

    def withdraw_coin(self, currency, amount, address, secondary_address='None', transaction_type='default', contain_req=False):
        """
        코인 출금
        :param currency: Currency symbol
        :param amount: 주문 가격
        :param address: 출금 지갑 주소
        :param secondary_address: 2차 출금주소 (필요한 코인에 한해서)
        :param transaction_type: 출금 유형
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/withdraws/coin"
            data = {"currency": currency,
                    "amount": amount,
                    "address": address,
                    "secondary_address": secondary_address,
                    "transaction_type": transaction_type}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def withdraw_cash(self, amount: str, contain_req=False):
        """
        현금 출금
        :param amount: 출금 액수
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/withdraws/krw"
            data = {"amount": amount}
            headers = self._request_headers(data)
            result = _send_post_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None

    def get_individual_withdraw_order(self, uuid: str, currency: str, contain_req=False):
        """
        현금 출금
        :param uuid: 출금 UUID
        :param txid: 출금 TXID
        :param currency: Currency 코드
        :param contain_req: Remaining-Req 포함여부
        :return:
        """
        try:
            url = "https://api.bithumb.com/v1/withdraw"
            data = {"uuid": uuid, "currency": currency}
            headers = self._request_headers(data)
            result = _send_get_request(url, headers=headers, data=data)
            if contain_req:
                return result
            else:
                return result[0]
        except Exception as x:
            print(x.__class__.__name__)
            logger.info(result)
            return None


if __name__ == "__main__":
    import pprint
    with open("bithumb_home.txt") as f:
        lines = f.readlines()
        access = lines[0].strip()
        secret = lines[1].strip()

    # Exchange API 사용을 위한 객체 생성
    bithumb = bithumb(access, secret)

    #-------------------------------------------------------------------------
    # Exchange API
    #-------------------------------------------------------------------------
    # 자산 - 전체 계좌 조회
    balances = bithumb.get_order("KRW-XRP")
    pprint.pprint(balances)

    # order = upbit.get_order('50e184b3-9b4f-4bb0-9c03-30318e3ff10a')
    # print(order)
    # # 원화 잔고 조회
    # print(upbit.get_balance(ticker="KRW"))          # 보유 KRW
    # print(upbit.get_amount('ALL'))                  # 총매수금액
    # print(upbit.get_balance(ticker="KRW-BTC"))      # 비트코인 보유수량
    # print(upbit.get_balance(ticker="KRW-XRP"))      # 리플 보유수량

    #print(upbit.get_chance('KRW-HBAR'))
    #print(upbit.get_order('KRW-BTC'))

    # 매도
    # print(upbit.sell_limit_order("KRW-XRP", 1000, 20))

    # 매수
    # print(upbit.buy_limit_order("KRW-XRP", 200, 20))

    # 주문 취소
    # print(upbit.cancel_order('82e211da-21f6-4355-9d76-83e7248e2c0c'))

    # 시장가 주문 테스트
    # upbit.buy_market_order("KRW-XRP", 10000)

    # 시장가 매도 테스트
    # upbit.sell_market_order("KRW-XRP", 36)

