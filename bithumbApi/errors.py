class BithumbError(Exception):
    def __str__(self):
        return "bithumb Base Error"


class CreateAskError(BithumbError):
    def __str__(self):
        return "주문 요청 정보가 올바르지 않습니다."


class CreateBidError(BithumbError):
    def __str__(self):
        return "주문 요청 정보가 올바르지 않습니다."


class InsufficientFundsAsk(BithumbError):
    def __str__(self):
        return "매수/매도 가능 잔고가 부족합니다."


class InsufficientFundsBid(BithumbError):
    def __str__(self):
        return "매수/매도 가능 잔고가 부족합니다."


class UnderMinTotalAsk(BithumbError):
    def __str__(self):
        return "주문 요청 금액이 최소 주문 금액 미만입니다."


class UnderMinTotalBid(BithumbError):
    def __str__(self):
        return "주문 요청 금액이 최소 주문 금액 미만입니다."


class WidthdrawAddressNotRegisterd(BithumbError):
    def __str__(self):
        return "허용되지 않은 출금 주소입니다."


class ValidationError(BithumbError):
    def __str__(self):
        return "잘못된 API 요청입니다."


class InvalidQueryPayload(BithumbError):
    def __str__(self):
        return "JWT 헤더의 페이로드가 올바르지 않습니다."


class JwtVerification(BithumbError):
    def __str__(self):
        return "JWT 헤더 검증에 실패했습니다."


class ExpiredAccessKey(BithumbError):
    def __str__(self):
        return "API 키가 만료되었습니다."


class NonceUsed(BithumbError):
    def __str__(self):
        return "이미 요청한 nonce값이 다시 사용되었습니다."


class NoAutorizationIP(BithumbError):
    def __str__(self):
        return "허용되지 않은 IP 주소입니다."


class OutOfScope(BithumbError):
    def __str__(self):
        return "허용되지 않은 기능입니다."


class TooManyRequests(BithumbError):
    def __str__(self):
        return "요청 수 제한을 초과했습니다."


def raise_error(code):
    if code == 429:
        raise TooManyRequests()
    else:
        raise BithumbError()