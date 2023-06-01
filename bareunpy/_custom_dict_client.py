from typing import List

import grpc
from google.protobuf.empty_pb2 import Empty

import bareun.custom_dict_pb2 as pb
import bareun.custom_dict_pb2_grpc as cds
import bareun.dict_common_pb2 as common



def build_dict_set(domain: str, name: str, dict_set: set) -> common.DictSet:
    """
    주어진 파라미터를 사용하여 사용자 사전의 한 표현 형태인 DictSet protobuf 메시지를 만듭니다.

    Args:
        domain (str): 사용자 사전의 이름
        name (str): 사용자 사전에 대한 설명
        dict_set (set): 사용자 사전에 들어가야 할 단어들의 잡합

    Returns:
        common.DictSet: protobuf DictSet 메시지
    """
    ret = common.DictSet()
    ret.name = domain + "-" + name
    ret.type = common.DictType.WORD_LIST
    for v in dict_set:
        ret.items[v] = 1
    return ret


MAX_MESSAGE_LENGTH = 100 * 1024 * 1024


class CustomDictionaryServiceClient:
    """
    커스텀 사전을 생성, 조회, 업데이트, 삭제하는 클라이언트
    
    The custom dictionary client which can create, update, list, delete your own one.
    """

    def __init__(self, channel: grpc.Channel, apikey:str):
        """사용자 사전을 관리하는 클라이언트 객체 생성자

        Args:
            remote (grpc.Channel): 미리 만들어 놓은 channel 객체
        """
        super().__init__()
        self.channel = channel
        self.apikey = apikey
        self.metadata=(
                ('api-key', self.apikey),
                )

        self.stub = cds.CustomDictionaryServiceStub(self.channel)


    def get_list(self) -> List[pb.CustomDictionaryMeta]:
        """사전 목록을 가져옵니다.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            List[pb.CustomDictionaryMeta]: 사전에 대한 정보들을 목록을 배열합니다.
        """
        req = Empty()
        try:
            res, c = self.stub.GetCustomDictionaryList.with_call(
                request=req, metadata=self.metadata)
            return res.domain_dicts
        except grpc.RpcError as e:
            raise e


    def get(self, domain: str) -> pb.CustomDictionary:
        """
        정의된 사용사 사전의 내용 전체를 가져온다.

        Args:
            domain (str): 사용자 사전이 이름

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.CustomDictionary: 사용자 사전 데이터 전체를 담고 있는 protobuf 메시지
        """
        req = pb.GetCustomDictionaryRequest()
        req.domain_name = domain
        try:
            res, c = self.stub.GetCustomDictionary.with_call(
                request=req, metadata=self.metadata)
            return res.dict
        except grpc.RpcError as e:
            raise e


    def update(self, domain: str, np: set, cp: set, cp_caret: set, vv: set, va: set) -> bool:
        """ 사용자 사전을 갱신합니다.

        Args:
            domain (str): 사용자 사전의 이름
            np (set): 고유명사 단어 집합
            cp (set): 복합명사 단어 집합
            cp_caret (set): 복합명사 분리 단어 집합
            vv (set): 동사 단어 집합
            va (set): 형용사 단어 집합

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            bool: 정상적으로 갱신되면 참을 돌려줍니다.
        """
        
        req = pb.UpdateCustomDictionaryRequest()
        req.domain_name = domain

        req.dict.domain_name = domain

        req.dict.np_set.CopyFrom(build_dict_set(domain, 'np-set', np))
        req.dict.cp_set.CopyFrom(build_dict_set(domain, 'cp-set', cp))
        req.dict.vv_set.CopyFrom(build_dict_set(domain, 'vv-set', vv))
        req.dict.va_set.CopyFrom(build_dict_set(domain, 'va-set', va))
        req.dict.cp_caret_set.CopyFrom(
            build_dict_set(domain, 'cp-caret-set', cp_caret))

        try:
            res, c = self.stub.UpdateCustomDictionary.with_call(
                request=req, metadata=self.metadata)
            return res.updated_domain_name == domain
        except grpc.RpcError as e:
            raise e


        """
        :return: 삭제된 도메인의 이름들
        """
    def remove_all(self) -> List[str]:
        """
        모든 커스텀 사전을 삭제한 다음 삭제한 사전의 이름을 돌려줍니다.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            List[str]: 삭제한 사전의 이름
        """
        req = pb.RemoveCustomDictionariesRequest()
        req.all = True

        try:
            res, c = self.stub.RemoveCustomDictionaries.with_call(
                request=req, metadata=self.metadata)
            return res.deleted_domain_names.keys()
        except grpc.RpcError as e:
            raise e

        """
        지정한 도메인의 커스텀 사전을 삭제한다.
        :param domains: 
        :return: 
        """
    def remove(self, domains: List[str]) -> List[str]:
        """ 지정한 도메인의 사용지 사전을 삭제한 다음 삭제한 사전의 목록을 반환합니다.

        Args:
            domains (List[str]): 삭제할 커스텀 사전의 이름들

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            List[str]: 정상 삭제된 도메인의 이름 목록을 돌려줍니다.
        """
        req = pb.RemoveCustomDictionariesRequest()
        req.domain_names.extend(domains)
        req.all = False
        try:
            res, c = self.stub.RemoveCustomDictionaries.with_call(
                request=req, metadata=self.metadata)
            return res.deleted_domain_names.keys()
        except grpc.RpcError as e:
            raise e
