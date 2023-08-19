import re
import json

from utils import pre_processing, post_processing, validate_json
from KoreanAddress import get_address
from langchain import PromptTemplate
from langchain.llms import OpenAI
import os

def inference(api_key,input, l,result_queue):
    # Define the JSON Schema
    result_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "resultList": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "seq": {
                        "type": "string",
                    },
                    "requestAddress": {
                        "type": "string"
                    },
                },
                "required": ["requestAddress","seq"]
            }
        }
    },
    "required": ["resultList"]
    }

    template = """
    |Start of task|
    - You will work on translating a non-refined address in English into refined Korean. 
    - Unrestricted English addresses can only be made in English or mixed with Korean.
    - Output are in json, generate an json that adheres to the schema {output_schema} and the translation is carried out according to the Rule.
    - You should write all the answers in Korean. There should be no less translated parts of English.
    - Please answer in order of wide area to narrow area.
    - You only need to interpret the words in the data to be translated. Only derive the result from the translation of requestAddress, you should not put any additional information.
    Please create the correct answer according to seq. The correct answer to each question is not related to the correct answer to the other question.
    Even if you can infer through another requestAddress, you should only translate it through the address shown in seq.
    - You must make it into a complete dict(). In the middle, '...' should not be created.
    |End of task|

    |Start of Rule|
    There are some rules when you translate.
    1. Addresses and requests may be mixed. The request may be in front of or behind the address. In the example below, "문 앞 배관실 넣어주세요" corresponds to the request. Delete requests.
    requestAddress : Incheon Tax Office, 75, Ugak-ro, Dong-gu, Incheon 문 앞 배관실 넣어주세요 -> requestAddress : 인천광역시 동구 우각로 75
    requestAddress : 배송전 전화주세요Jungbu Tax Office, 170, Toegye-ro, Jung-gu, Seoul -> requestAddress : 서울특별시 중구 퇴계로 170

    2. There may be a typo in the place name, as shown in the following example. "SOUL" is a typo of "Seoul".
    requestAddress : B 101 Sejong-daero Jung-gu SOUL -> requestAddress : 서울특별시 중구 세종대로 지하101
    
    3. "-ro", "-daero" is interpreted as "로", "대로". Most geographical names are translated as they are pronounced in English. "G" is usually pronounced as 'ㄱ', but it can also be pronounced as 'ㅈ' depending on the situation.
    requestAddress : Jongno Tax Office 22 Samil-daero 30-gil Jongno-gu Seoul노크를 3번하고 열려라 참깨를 외쳐주세요 -> requestAddress : 서울특별시 종로구 삼일대로30길 22    
    requestAddress : 지하 2 Sejong-daero Gung-gu Seoul -> requestAddress : 서울특별시 중구 세종대로 지하2
    requestAddress : 지하 300 Wangsimni-ro Seongdong구 Seoul -> requestAddress : 서울특별시 성동구 왕십리로 지하300
    requestAddress : Gwangyang 세관 House 22 Jungdong-ro Gwangyang-si Jeollanam-do -> requestAddress : 전라남도 광양시 중동로 22
    
    4. Words translated into English, such as "South Mountain" and "Ring-ro," may exist. This corresponds to "남산","순환로" respectively
    requestAddress : Gwangju Regional Joint Government Complex 43 Advanced Science and Technology Road 208beon-gil Buk-gu Gwangju1001ho1001동 -> requestAddress : 광주광역시 북구 첨단과기로208번길 43
    requestAddress : B, 2089, Nambu Ring-ro, Dongjak-gu, Seoul -> requestAddress : 서울특별시 동작구 남부순환로 지하2089

    5. You only need to interpret the words in the data to be translated. Only derive the result from the translation of requestAddress, you should not put any additional information.
    Please create the correct answer according to seq. The correct answer to each question is not related to the correct answer to the other question.
    Even if you can infer through another requestAddress, you should only translate it through the address shown in seq.
    "Only derive the result from the translation of requestAddress, you should not put any additional information.
    Please create the correct answer according to seq."
    requestAddress : 359 Jongno-gu Jongno-gu Seoul 101동 -> requestAddress : 서울특별시 종로구 359 
    requestAddress : B 1822 김&장 -> requestAddress : 지하 1822
    requestAddress :  Jingwan 2-ro 15-25B Seoul (Jingwan-dong) -> requestAddress : 서울특별시 진관2로 지하15-25
    requestAddress : 지하 156 Seoul -> requestAddress : 서울특별시 지하 156
    
    In the first example, Please translate "Seoul" -> "서울특별시"  "Jongno-gu" -> "종로구" "359" -> "359" and the result is "서울특별시 종로구 359".
    In the second example, Please translate "B" -> "지하"  "1822" -> "1822" and the result is "지하 1822".
    In the third example, Please translate "Jingwan 2-ro" -> "진관2로"  "15-25B" -> "지하15-25" "Seoul" -> "서울특별시" and the result is "서울특별시 진관2로 지하15-25".
    In the fourth example, Please translate "지하 156" -> "지하 156"  "Seoul" -> "서울특별시"  and the result is "서울특별시 지하 156".
    
    6. If "지하","B", "underground" or others exists in the unstructured address, they mean underground. If there's an underground meaning, please mark "지하"
    If you don't have a word that means underground, you don't add it.
    requestAddress : 127 지하 Seosomun-ro Jung-gu 새울 -> requestAddress : 서울특별시 중구 서소문로 지하127
    requestAddress : GF160 Yanghwa-ro 마포-gu Seoul -> requestAddress : 서울특별시 마포구 양화로 지하160
    requestAddress : Daelim-ro 2 Dongjak-gu Seoul 100 office -> requestAddress : 서울특별시 동작구 대림로 2
    
    |End of Rule|

    - You should write all the answers in Korean. There should be no less translated parts of English.    
    - You only need to interpret the words in the data to be translated. Only derive the result from the translation of requestAddress, you should not put any additional information.
    Please create the correct answer according to seq. The correct answer to each question is not related to the correct answer to the other question.
    Even if you can infer through another requestAddress, you should only translate it through the address shown in seq.
    - You should write all the answers in Korean. There should be no less translated parts of English.
    - Please answer in order of wide area to narrow area.
    - You must make it into a complete dict(). In the middle, '...' should not be created.
    
    Input:
    {Address_Input}
    """

    # 전처리 추가
    pre_data = dict()
    pre_data["requestList"] = [{"seq":i["seq"],"requestAddress":pre_processing(i["requestAddress"])}for i in input["requestList"]]
    # print("전처리 수행")
    # print(pre_data)
    state = False

    while(not state):
        prompt = PromptTemplate(
            input_variables=["Address_Input", "output_schema"],
            template=template,
        )
        prompt = prompt.format(Address_Input=pre_data, output_schema=result_schema)   

        fail_code = 1
        fail_count = 0     
        
        temperature_value = 0.4
        while fail_code:
            llm = OpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature = temperature_value,
                    max_tokens = 1000,
                    top_p = 0.3,
                )
            result = llm(prompt)

            del llm
            
            try:
                result = re.sub(r'\n',' ',result)
                result = re.sub(r'\s+',' ',result)
                result = re.sub(r"\'",'\"',result)
                result = json.loads(result)
                fail_code = 0
            except:
                print(result)
                fail_count+=1
                temperature_value += 0.1
                if fail_count >3:
                    raise ValueError

        state = validate_json(result, result_schema) and (len(input['requestList']) == len(result['resultList']))
        
    post_data = [{'seq': i["seq"], 'requestAddress' : post_processing(i["requestAddress"]),'ChatGPTAddress' : i["requestAddress"]} for i in result["resultList"]]
    # print("chat 실행")
    # print(post_data)
    # 도로명 주소 api 실행 후
    api_result = [{"seq":i['seq'],"resultAddress":get_address(api_key,i['requestAddress'])} for i in post_data]

    l.acquire()
    try:
        result_queue.put(api_result)
    finally:
        l.release()