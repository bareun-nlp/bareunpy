# -*- coding: utf-8 -*-

from typing import List
import grpc
from ._custom_dict_client import CustomDictionaryServiceClient
from bareun.custom_dict_pb2 import CustomDictionary
from bareun.dict_common_pb2 import DictSet


def read_dic_file(fn :str) -> set:
    """
    사용자 사전의 파일을 읽어들입니다.

    Args:
        fn (str): 사용자 사전 파일 이름

    Returns:
        set: 사용자 사전을 set 형식으로 만들어서 돌려줍니다.
    """
    dict_set = set()
    with open(fn, 'r') as r:
        while True:
            w = r.readline()
            if not w:
                break
            if w[0] != '#':
                w2 = w.strip()
                if len(w2) > 0:
                    dict_set.add(w2)
    return dict_set


def pb_map_to_set(ds: DictSet) -> set:
    """
    DictSet을 사전으로 변환합니다.

    Args:
        ds (DictSet): DictSet 객체

    Returns:
        set: 중복이 없는 사전 객체
    """
    ret = set()
    for k in ds.items.keys():
        ret.add(k)
    return ret

class CustomDict():
    """
    사용자 사전을 쉽게 사용하도록 해주는 래퍼(wrapper).

    'CustomDict' .
    :ref:`optional-installations`.
    .. code-block:: python
        :emphasize-lines: 1
        >>> import bareunpy as brn
        >>> tagger = brn.Tagger()
        >>> cd = tagger.custom_dict("law")
        >>> # or
        >>> cd = brn.CustomDict("law", "localhost", 5656)
        >>> cd.read_cp_set_from_file("my_np_set.txt")
        >>> cd.copy_cp_set(set(['새단어', '코로나19', 'K방역']))
        >>> cd.read_cp_caret_set_from_file('my_cp_caret.txt')
        >>> cd.copy_vv_set(set(['카톡하', '신박하다']))
        >>> cd.copy_va_set(set(['드라마틱하', '판타스틱하']))
        >>> cd.update()
        >>> ## copy data from server
        >>> cd2 = tagger.custom_dict("law")
        >>> custom_dict = cd2.get()
        >>> # cd2.save(dir="my_dir")
    """

    def __init__(self, apikey:str, domain: str, channel: grpc.Channel):
        """
        사용자 사전 래퍼(wrapper)의 생성자

        Args:
            domain (str): 사용자 사전의 이름, 반드시 지정되어야 합니다.
            channel(grpc.Channel): 원격에 연결할 정보
        Raises:
            ValueError: 사용자 사전의 이름이 없으면 에러를 발생시킵니다.
        """
        self.domain = domain
        if domain is None:
            raise ValueError("domain name must be specified.")

        self.stub = CustomDictionaryServiceClient(channel, apikey)
        self.cp_set = set()
        self.np_set = set()
        self.cp_caret_set = set()
        self.vv_set = set()
        self.va_set = set()

    def read_np_set_from_file(self, fn: str):
        """
        고유명사 사전을 파일에서 읽어들입니다.

        이 파일은 한줄에 하나의 사전입니다. '#'로 시작하는 줄은 무시합니다.

        Args:
            fn (str): 고유명사 파일 이름
        """
        self.np_set = read_dic_file(fn)

    def read_cp_set_from_file(self, fn: str):
        """
        복합명사 사전을 파일에서 읽어들입니다.

        이 파일은 한줄에 하나의 사전입니다. '#'로 시작하는 줄은 무시합니다.

        Args:
            fn (str): 복합명사 파일 이름
        """
        self.cp_set = read_dic_file(fn)

    def read_cp_caret_set_from_file(self, fn: str):
        """
        복합명사 분리 사전을 파일에서 읽어들입니다.

        이 파일은 한줄에 하나의 사전입니다. '#'로 시작하는 줄은 무시합니다.

        Args:
            fn (str): 복합명사 분리 사전 파일 이름
        """
        self.cp_caret_set = read_dic_file(fn)

    def read_vv_set_from_file(self, fn: str):
        """
        동사 사전을 파일에서 읽어들입니다.

        이 파일은 한줄에 하나의 사전입니다. '#'로 시작하는 줄은 무시합니다.

        Args:
            fn (str): 동사 사전 파일 이름
        """
        self.vv_set = read_dic_file(fn)

    def read_va_set_from_file(self, fn: str):
        """
        형용사 사전을 파일에서 읽어들입니다.

        이 파일은 한줄에 하나의 사전입니다. '#'로 시작하는 줄은 무시합니다.

        Args:
            fn (str): 형용사 사전 파일 이름
        """
        self.va_set = read_dic_file(fn)

    def copy_np_set(self, dict_set: set):
        """
        집합을 고유명사 사전으로 지정합니다.

        Args:
            dict_set (set): 고유명사 사전
        """
        self.np_set = dict_set

    def copy_cp_set(self, dict_set: set):
        """
        집합을 복합명사 사전으로 지정합니다.

        Args:
            dict_set (set): 복합명사 사전
        """
        self.cp_set = dict_set

    def copy_cp_caret_set(self, dict_set: set):
        """
        집합을 복합명사 분리 사전으로 지정합니다.

        Args:
            dict_set (set): 복합명사 분리 사전
        """
        self.cp_caret_set = dict_set

    def copy_vv_set(self, dict_set: set):
        """
        집합을 동사 사전으로 지정합니다.

        Args:
            dict_set (set): 동사 사전
        """
        self.vv_set = dict_set

    def copy_va_set(self, dict_set: set):
        """
        집합을 형용사 사전으로 지정합니다.

        Args:
            dict_set (set): 형용사 사전
        """
        self.va_set = dict_set

    def update(self) -> bool:
        """
        복합명사 사전을 바이칼 NLP 서버에 갱신합니다.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            bool: 갱신이 성공하면 참을 돌려줍니다.
        """
        return self.stub.update(self.domain,
                                self.np_set,
                                self.cp_set,
                                self.cp_caret_set,
                                self.vv_set,
                                self.va_set)

    def get(self) -> CustomDictionary:
        """
        사용자 사전의 내용을 가져옵니다.
        가져온 결과는 현재 설정된 사전의 내용을 반영하지 않습니다.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.CustomDictionary: 사용자 사전 데이터 전체를 담고 있는 protobuf 메시지
        """
        return self.stub.get(self.domain)


    def load(self):
        """
        서버에 저정되어 있는 사용자 사전을 모두 가져옵니다.
        """
        try:
            d = self.stub.get(self.domain)
            self.np_set = pb_map_to_set(d.np_set)
            self.cp_caret_set = pb_map_to_set(d.cp_caret_set)
            self.cp_set = pb_map_to_set(d.cp_set)
        except Exception as e:
            pass


    def clear(self) -> List[str]:
        """
        사용자 사전의 내용을 삭제합니다.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            List[str]: 삭제한 사용자 사전의 이름
        """

        self.np_set.clear()
        self.cp_set.clear()
        self.cp_caret_set.clear()
        return self.stub.remove([self.domain])
