# 웰니스 관광 데이터 가져오기

# import requests
# import pandas as pd
#
# url = "https://apis.data.go.kr/B551011/WellnessTursmService/areaBasedList"
#
# params = {
#     "serviceKey": "b28907c1ea9702f6a4e079b75f571f93ed3220b3fe6b83205004f7842e91046e",
#     "numOfRows": "200",  # 전체 데이터가 176개이므로 200으로 설정하면 한 번에 다 가져옵니다.
#     "pageNo": "1",
#     "MobileOS": "ETC",
#     "MobileApp": "AppTest",
#     "_type": "json",
#     "langDivCd": "ko"
# }
#
# try:
#     response = requests.get(url, params=params)
#     data = response.json()
#
#     # 데이터 추출
#     items = data['response']['body']['items']['item']
#     df = pd.DataFrame(items)
#
#     # --- 여기서부터 추가/수정 ---
#     # 1. 화면에 출력
#     print(f"총 {len(df)}건의 데이터를 가져왔습니다.")
#
#     # 2. 엑셀로 저장 (파일명: wellness_data.xlsx)
#     # openpyxl 라이브러리가 필요할 수 있습니다: pip install openpyxl
#     df.to_excel("wellness_data.xlsx", index=False)
#     print("성공적으로 엑셀 파일이 저장되었습니다!")
#
# except Exception as e:
#     print(f"에러 발생: {e}")


# 내주변 힐링스팟찾기, 테마별 맞춤 추천 이런걸 긁어오는 코드
import requests
import pandas as pd

# 1. 설정 및 인증키
SERVICE_KEY = "b28907c1ea9702f6a4e079b75f571f93ed3220b3fe6b83205004f7842e91046e"
BASE_URL = "https://apis.data.go.kr/B551011/WellnessTursmService"


# 2. 함수 정의 (반드시 호출하는 코드보다 위에 있어야 함)
def get_wellness_by_location(mapX, mapY, radius=10000):
    url = f"{BASE_URL}/locationBasedList"
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": "20",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "AppTest",
        "_type": "json",
        "listYN": "Y",
        "arrange": "E",
        "mapX": str(mapX),
        "mapY": str(mapY),
        "radius": str(radius),
        "langDivCd": "ko"
    }
    response = requests.get(url, params=params)
    res_json = response.json()
    if 'response' in res_json and 'body' in res_json['response']:
        items = res_json['response']['body']['items']['item']
        return pd.DataFrame(items)
    else:
        return pd.DataFrame()


def get_wellness_by_keyword(keyword):
    url = f"{BASE_URL}/searchKeyword"
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": "20",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "AppTest",
        "_type": "json",
        "keyword": keyword,
        "langDivCd": "ko"
    }
    response = requests.get(url, params=params)
    res_json = response.json()
    if 'response' in res_json and 'body' in res_json['response']:
        items = res_json['response']['body']['items']['item']
        return pd.DataFrame(items)
    else:
        return pd.DataFrame()


# 3. 실제 실행부 (함수들이 정의된 후 가장 아래에서 호출)
if __name__ == "__main__":
    print("📍 내 주변 힐링 스팟 검색 중...")

    my_x = 126.9780  # 경도
    my_y = 37.5665  # 위도

    # 이제 정의가 되어 있으므로 에러가 나지 않아
    around_me_df = get_wellness_by_location(my_x, my_y)

    if not around_me_df.empty:
        print("\n--- [내 주변 추천 결과] ---")
        print(around_me_df[['title', 'baseAddr']].head())

    print("\n🌲 '숲' 테마 검색 중...")
    forest_df = get_wellness_by_keyword("숲")
    if not forest_df.empty:
        print("\n--- [키워드 '숲' 검색 결과] ---")
        print(forest_df[['title', 'baseAddr']].head())