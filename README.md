# CJ대한통운 미래기술챌린지 2023
프로젝트명 : 비정제 영문 주소 AI 번역 시스템
개발 기간 : 23.07.03 ~ 23.08.15

## 배포 주소
https://cj-gandj.du.r.appspot.com

## 프로젝트 소개
저희 프로젝트는 사용자가 비정제된 다양한 형식의 영문 주소를 요청 시, AI가 한국 주소 체계에 맞게 도로명주소 형태로 번역해 반환하는 시스템을 구현하고자 합니다.

## Stacks

### Environment
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-007ACC?style=for-the-badge&logo=Visual%20Studio%20Code&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=Git&logoColor=white)
![Github](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=Postman&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=GoogleCloud&logoColor=white)

### Development
![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-00897B?style=for-the-badge&logo=FastAPI&logoColor=white)
### Communication
![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=Notion&logoColor=white)

## Request & Response 형식

### Request
```
{
    "requestList": [
        {
            "seq": int,
            "requestAddress": "char"
        }
    ]
}
```

### Response
```
{
    "HEADER": {
        "RESULT_CODE": "char",
        "RESULT_MSG": "char"
    },
    "BODY": [
        {
            "seq": "char",
            "resultAddress": "char"
        }
    ]
}
```

## Interface Definition
- Interface Type : HTTP RESTful
- Method : POST
- Data Set : JSON
- Character-set : UTF-8
- ContentType : application/json/x-www-form-urlencoded


