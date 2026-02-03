import os

import requests
from dotenv import load_dotenv

load_dotenv()


def collect_comments(video_id):
    # YouTube 댓글 수집하기
    # 1. 변수 설정
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"

    part = "snippet"
    videoId = video_id  # 댓글 수집할 영상
    key = os.getenv("YOUTUBE_API_KEY")
    maxResults = 100  # 최대 100개
    textFormat = "plainText"
    nextPageToken = None

    data_list = []
    max_rep = 10

    # ... (앞부분 동일)

    # 2. 반복문 시작
    for i in range(max_rep):
        print(f"{i + 1} 번째 데이터 수집을 시작합니다.")

        # f-string 사용 시 nextPageToken이 None인 경우 'None' 문자열이 들어가는 것을 방지하기 위해 params 방식 추천
        params = {
            "part": part,
            "videoId": videoId,
            "key": key,
            "maxResults": maxResults,
            "textFormat": textFormat,
            "pageToken": nextPageToken,  # None이면 무시됨
        }

        # 3. API 요청
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            # 5. nextPageToken 업데이트
            nextPageToken = data.get("nextPageToken")

            # 6. 댓글 텍스트만 추출
            items = data.get("items", [])
            comments_only = []
            for item in items:
                # topLevelComment의 snippet 안에 있는 textDisplay(또는 textOriginal)만 가져옴
                comment_text = item["snippet"]["topLevelComment"]["snippet"][
                    "textDisplay"
                ]
                comments_only.append(comment_text)

            print(f"\t{len(comments_only)} 개의 댓글을 수집했습니다.")

            # 7. 전체 리스트에 합치기
            data_list.extend(comments_only)

            if not nextPageToken:
                print("다음 페이지가 없어 종료합니다.")
                break
        else:
            print(f"에러 발생: {response.status_code}")
            break

    # 결과 확인 (상위 5개만 출력)
    print(f"\n총 {len(data_list)}개의 댓글이 수집되었습니다.")
    print(data_list[:5])
