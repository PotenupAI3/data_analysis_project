from __future__ import annotations

from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from konlpy.tag import Okt
from PIL import Image
from wordcloud import WordCloud


def word_cloud(data_list, stopwords, mask_img_path):
    okt = Okt()
    all_comments = " ".join(data_list)
    nouns = okt.nouns(all_comments)
    filtered_nouns = [n for n in nouns if n not in stopwords and len(n) > 1]
    count = Counter(filtered_nouns)

    font_path = "C:/Windows/Fonts/malgun.ttf"

    image = Image.open(mask_img_path)
    mask_img = np.array(image)

    wc = WordCloud(
        font_path=font_path,
        background_color="black",
        mask=mask_img,  # 전처리된 마스크 적용
        width=800,
        height=800,
        # contour_width=2,       # 테두리 선을 넣고 싶다면 추가
        # contour_color='black'
    )

    print("워드클라우드 생성 중...")
    img = wc.generate_from_frequencies(count)

    plt.figure(figsize=(8, 8))
    plt.imshow(img, interpolation="bilinear")  # interpolation은 bilinear 권장
    plt.axis("off")
    plt.show()
