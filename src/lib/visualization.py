from collections import Counter

import matplotlib.pyplot as plt
from konlpy.tag import Okt
from wordcloud import WordCloud


def word_cloud(data_list, stopwords):
    # 1. 명사 추출 (KoNLPy 사용)
    okt = Okt()
    all_comments = " ".join(data_list)  # 리스트를 하나의 문자열로 합침
    nouns = okt.nouns(all_comments)  # 명사만 추출

    # 2. 불용어(Stopwords) 제거
    # 의미 없는 단어(예: '진짜', '정말', '것')를 필터링합니다.
    # stopwords = [
    #     "진짜",
    #     "정말",
    #     "영상",
    #     "채널",
    #     "구독",
    #     "좋아요",
    #     "댓글",
    #     "보고",
    #     "수",
    #     "거",
    #     "나",
    #     "서울",
    #     "지방",
    #     "사람",
    #     "인구",
    # ]
    filtered_nouns = [n for n in nouns if n not in stopwords and len(n) > 1]

    # 3. 빈도수 계산
    count = Counter(filtered_nouns)

    # 4. 워드클라우드 설정
    # 한글 깨짐 방지를 위해 시스템의 한글 폰트 경로를 지정해야 합니다.
    # Windows: 'C:/Windows/Fonts/malgun.ttf' / Mac: '/Library/Fonts/Arial Unicode.ttf'
    font_path = "C:/Windows/Fonts/malgun.ttf"

    wc = WordCloud(
        font_path=font_path,
        background_color="white",
        width=800,
        height=600,
        colormap="viridis",  # 색상 테마
    )

    # 5. 이미지 생성 및 출력
    print("워드클라우드 생성 중...")
    img = wc.generate_from_frequencies(count)

    plt.figure(figsize=(10, 8))
    plt.imshow(img, interpolation="spline16")  # 보간법 설정
    plt.axis("off")  # 축 숨기기
    plt.show()
