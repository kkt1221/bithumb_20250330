import re
import requests
import time

getframe_expr = 'sys._getframe({}).f_code.co_name'


def _parse_remaining_req(remaining_req):
    """

    :param remaining_req:
    :return:
    """
    try:
        p = re.compile("group=([a-z]+); min=([0-9]+); sec=([0-9]+)")
        m = p.search(remaining_req)
        return m.group(1), int(m.group(2)), int(m.group(3))
    except:
        return None, None, None


def _call_public_api(url, **kwargs):
    """

    :param url:
    :param kwargs:
    :return:
    """
    try:
        resp = requests.get(url, params=kwargs)
        remaining_req_dict = {}
        remaining_req = resp.headers.get('Remaining-Req')
        if remaining_req is not None:
            group, min, sec = _parse_remaining_req(remaining_req)
            remaining_req_dict['group'] = group
            remaining_req_dict['min'] = min
            remaining_req_dict['sec'] = sec
        contents = resp.json()
        return contents, remaining_req_dict
    except Exception as x:
        print("It failed", x.__class__.__name__)
        return None


def _send_post_request(url, headers=None, data=None):
    """

    :param url:
    :param headers:
    :param data:
    :return:
    """
    try:
        resp = requests.post(url, data=data, headers=headers)
        remaining_req_dict = {}
        remaining_req = resp.headers.get('Remaining-Req')
        if remaining_req is not None:
            group, min, sec = _parse_remaining_req(remaining_req)
            remaining_req_dict['group'] = group
            remaining_req_dict['min'] = min
            remaining_req_dict['sec'] = sec
        contents = resp.json()
        return contents, remaining_req_dict
    except Exception as x:
        print("send post request failed", x.__class__.__name__)
        print("caller: ", eval(getframe_expr.format(2)))
        return None


def _send_get_request(url, headers=None, data=None):
    """

    :param url:
    :param headers:
    :return:
    """
    retry_attempt = 0  # 재시도 횟수
    max_retries = 1  # 최대 재시도 횟수
    while retry_attempt <= max_retries:

        try:
            resp = requests.get(url, headers=headers, data=data)
            remaining_req_dict = {}
            remaining_req = resp.headers.get('Remaining-Req')
            if remaining_req is not None:
                group, min, sec = _parse_remaining_req(remaining_req)
                remaining_req_dict['group'] = group
                remaining_req_dict['min'] = min
                remaining_req_dict['sec'] = sec
            contents = resp.json()
            return contents, remaining_req_dict
        except Exception as x:
            if retry_attempt < max_retries:
                retry_attempt += 1
                print(f"_send_get_request Request failed. Retrying {retry_attempt}/{max_retries}...")
                time.sleep(3)  # 재시도 전 대기 시간 (필요시 조정 가능)
            else:
                print("send get request failed", x.__class__.__name__)
                print("caller: ", eval(getframe_expr.format(2)))
                return None


def _send_delete_request(url, headers=None, data=None):
    """

    :param url:
    :param headers:
    :param data:
    :return:
    """
    try:
        resp = requests.delete(url, headers=headers, data=data)
        remaining_req_dict = {}
        remaining_req = resp.headers.get('Remaining-Req')
        if remaining_req is not None:
            group, min, sec = _parse_remaining_req(remaining_req)
            remaining_req_dict['group'] = group
            remaining_req_dict['min'] = min
            remaining_req_dict['sec'] = sec
        contents = resp.json()
        return contents, remaining_req_dict
    except Exception as x:
        print("send delete request failed", x.__class__.__name__)
        print("caller: ", eval(getframe_expr.format(2)))
        return None
