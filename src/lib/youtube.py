import os
import random
import time

import requests

YOUTUBE_COMMENTTHREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
YOUTUBE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/comments"

__all__ = [
    "collect_all_comments",
    "_fetch_all_replies",
    "YOUTUBE_COMMENTTHREADS_URL",
    "YOUTUBE_COMMENTS_URL",
]


# 사용 예시:
# rows, texts = collect_all_comments("VIDEO_ID_HERE", include_replies=True)
# print(len(rows), len(texts))
def collect_all_comments(
    video_id, api_key=None, include_replies=True, sleep=0.05, max_total=None
):
    """
    video_id의 댓글을 (최상위 + 대댓글) 끝까지 수집
    - include_replies=True면 대댓글도 전부 수집
    - max_total: 너무 많을 때 안전장치(원하면 None)
    """
    api_key = api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError(
            "YOUTUBE_API_KEY가 없습니다. 환경변수 또는 api_key 인자로 넣어주세요."
        )

    session = requests.Session()
    rows = []

    page_token = None
    page = 0

    while page_token:
        page += 1
        print(f"[threads] page {page} 수집 중...")

        params = {
            "part": "snippet",  # 최상위 댓글 스니펫
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "key": api_key,
            "pageToken": page_token,
            # "order": "time",            # 필요하면 time/relevance 선택
        }

        data = _request_json(YOUTUBE_COMMENTTHREADS_URL, params, session=session)

        # 참고: 여기 totalResults는 "최상위 댓글 수"인 경우가 많습니다.
        page_info = data.get("pageInfo", {})
        if page == 1:
            print(f"[info] pageInfo = {page_info}")

        items = data.get("items", [])
        for it in items:
            thread_sn = it.get("snippet", {})
            top = thread_sn.get("topLevelComment", {})
            top_sn = top.get("snippet", {})

            top_comment_id = top.get("id")
            rows.append(
                {
                    "comment_id": top_comment_id,
                    "parent_id": None,
                    "author": top_sn.get("authorDisplayName"),
                    "published_at": top_sn.get("publishedAt"),
                    "like_count": top_sn.get("likeCount"),
                    "text": top_sn.get("textDisplay") or top_sn.get("textOriginal"),
                }
            )

            # 대댓글 전부 수집(권장 방식: comments.list with parentId)
            if include_replies:
                reply_count = thread_sn.get("totalReplyCount", 0)
                if reply_count and top_comment_id:
                    reply_rows = _fetch_all_replies(
                        parent_id=top_comment_id,
                        api_key=api_key,
                        session=session,
                        sleep=sleep,
                    )
                    rows.extend(reply_rows)

            if max_total and len(rows) >= max_total:
                print(f"[stop] max_total={max_total} 도달로 중단합니다.")
                texts = [r["text"] for r in rows if r.get("text")]
                return rows, texts

        page_token = data.get("nextPageToken")

        if sleep:
            time.sleep(sleep)

    texts = [r["text"] for r in rows if r.get("text")]
    print(f"\n✅ 총 {len(rows)}개(최상위+대댓글) 댓글 수집 완료")
    print("샘플 5개:", texts[:5])
    return rows, texts


def _fetch_all_replies(parent_id, api_key, session=None, sleep=0.05):
    """
    특정 최상위 댓글(parent_id)의 대댓글을 comments.list로 전부 가져옴 (페이지네이션)
    """
    all_rows = []
    page_token = None
    page = 0

    while page_token:
        page += 1
        params = {
            "part": "snippet",
            "parentId": parent_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "key": api_key,
            "pageToken": page_token,
        }

        data = _request_json(YOUTUBE_COMMENTS_URL, params, session=session)

        items = data.get("items", [])
        for it in items:
            sn = it.get("snippet", {})
            all_rows.append(
                {
                    "comment_id": it.get("id"),
                    "parent_id": sn.get("parentId"),
                    "author": sn.get("authorDisplayName"),
                    "published_at": sn.get("publishedAt"),
                    "like_count": sn.get("likeCount"),
                    "text": sn.get("textDisplay") or sn.get("textOriginal"),
                }
            )

        page_token = data.get("nextPageToken")

        if sleep:
            time.sleep(sleep)

    return all_rows


def _request_json(url, params, session=None, max_retries=5, timeout=20):
    # 간단한 재시도 + 지수 백오프(429/5xx 대응)

    sess = session or requests.Session()

    # pageToken이 None이면 아예 params에서 제거 (가끔 더 안전)
    if params.get("pageToken") is None:
        params.pop("pageToken", None)

    for attempt in range(max_retries):
        resp = sess.get(url, params=params, timeout=timeout)

        # 성공
        if resp.status_code == 200:
            return resp.json()

        # 일시적 오류(레이트리밋/서버오류)면 재시도
        if resp.status_code in (429, 500, 502, 503, 504):
            sleep_s = (2**attempt) + random.uniform(0.0, 0.8)
            print(f"[retry] {resp.status_code} -> {sleep_s:.2f}s sleep")
            time.sleep(sleep_s)
            continue

        # 그 외 오류는 바로 중단 (메시지 출력)
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise RuntimeError(f"Request failed: {resp.status_code} / {err}")

    raise RuntimeError(f"Max retries exceeded for {url}")
