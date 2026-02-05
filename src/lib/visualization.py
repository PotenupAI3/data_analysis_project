from __future__ import annotations

from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from konlpy.tag import Okt
from PIL import Image
from wordcloud import WordCloud


def color_func(word, *args, **kwargs):
    if word in ["전주", "완주", "통합"]:
        return "#FF5501"
    else:
        return "#F8F8F8"


def word_cloud(data_list, stopwords, mask_img_path):
    okt = Okt()
    all_comments = " ".join(data_list)
    nouns = okt.nouns(all_comments)
    filtered_nouns = [n for n in nouns if n not in stopwords and len(n) > 1]
    count = Counter(filtered_nouns)

    font_path = "C:/Windows/Fonts/malgun.ttf"

    img = Image.open(mask_img_path).convert("L")
    arr = np.array(img)

    thr = 230  # 200~245 사이에서 조절
    mask_img = np.where(arr < thr, 0, 255).astype(np.uint8)

    wc = WordCloud(
        font_path=font_path,
        background_color="black",
        # background_color="#0B3D91",
        # background_color="#0A1F44",
        # colormap="plasma",
        # background_color="#0B3D91",
        mask=mask_img,  # 전처리된 마스크 적용
        width=800,
        height=800,
        # colormap="YlGn",
        contour_width=3,  # 테두리 선을 넣고 싶다면 추가
        contour_color="#E3F2FD",
        # contour_color="#90CAF9",
        max_font_size=200,
        min_font_size=8,
        color_func=color_func,
    )

    print("워드클라우드 생성 중...")
    img = wc.generate_from_frequencies(count)

    plt.figure(figsize=(8, 8))
    # plt.imshow(mask_img, cmap="gray")  # 육지 영역
    # plt.imshow(wc, alpha=1)
    plt.imshow(img, interpolation="bilinear")  # interpolation은 bilinear 권장
    plt.axis("off")
    plt.show()
