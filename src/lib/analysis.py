from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
from kiwipiepy import Kiwi
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


def market_basket_ko(
    texts: Sequence[str],
    *,
    min_support: float = 0.02,
    max_len: int = 2,
    metric: str = "lift",
    min_threshold: float = 1.0,
    top_k: int = 20,
    stop_noun: Iterable[str] = (),
    min_token_len: int = 2,
    sort_by: str = "lift",
    ascending: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    한국어 텍스트 리스트에서 명사 기반 연관규칙을 생성한다.

    Returns:
        {
          "rules": 연관규칙 DataFrame (정렬/상위 top_k는 별도로 'top_rules'에),
          "top_rules": 정렬 후 상위 top_k 규칙,
          "pivot_data": top_rules 기반 lift(또는 sort_by) 피벗 테이블,
          "frequent_itemsets": apriori 결과
        }
    """
    if not texts:
        empty = pd.DataFrame()
        return {
            "rules": empty,
            "top_rules": empty,
            "pivot_data": empty,
            "frequent_itemsets": empty,
        }

    kiwi = Kiwi()
    STOP = set(stop_noun)

    def _clean_ko(text: str) -> str:
        # ✅ 기존에 쓰던 _clean_ko가 이미 있으면 이 함수 삭제하고 그걸 사용해도 됨.
        # 기본값: 공백 정리 정도만 (너무 공격적인 정제는 키워드 손실)
        return " ".join(str(text).strip().split())

    def nouns_kiwi(text: str) -> list[str]:
        text = _clean_ko(text)
        tokens = kiwi.tokenize(text)
        nouns = [t.form for t in tokens if t.tag.startswith("NN")]
        nouns = [n for n in nouns if len(n) >= min_token_len and n not in STOP]
        return nouns

    # 1) 텍스트 -> 트랜잭션(명사 리스트)
    items_list = [nouns_kiwi(t) for t in texts]
    # 완전 빈 트랜잭션만 있는 경우 방지
    if all(len(items) == 0 for items in items_list):
        empty = pd.DataFrame()
        return {
            "rules": empty,
            "top_rules": empty,
            "pivot_data": empty,
            "frequent_itemsets": empty,
        }

    # 2) One-hot 인코딩
    te = TransactionEncoder()
    te_arr = te.fit(items_list).transform(items_list)
    df = pd.DataFrame(te_arr, columns=te.columns_)

    # 3) Apriori (빈발 항목)
    frequent_itemsets = apriori(
        df, min_support=min_support, use_colnames=True, max_len=max_len
    )
    if frequent_itemsets.empty:
        empty = pd.DataFrame()
        return {
            "rules": empty,
            "top_rules": empty,
            "pivot_data": empty,
            "frequent_itemsets": frequent_itemsets,
        }

    # 4) 연관규칙
    rules = association_rules(
        frequent_itemsets, metric=metric, min_threshold=min_threshold
    )
    if rules.empty:
        empty = pd.DataFrame()
        return {
            "rules": rules,
            "top_rules": rules,
            "pivot_data": empty,
            "frequent_itemsets": frequent_itemsets,
        }

    # 5) 보기 좋게: frozenset -> 문자열
    def _fs_to_str(fs) -> str:
        # frozenset({'단어'}) 또는 frozenset({'단어1','단어2'})를 '단어1,단어2'로
        return ",".join(sorted(list(fs)))

    rules = rules.copy()
    rules["antecedents_str"] = rules["antecedents"].apply(_fs_to_str)
    rules["consequents_str"] = rules["consequents"].apply(_fs_to_str)

    # 6) 정렬 + Top K
    if sort_by not in rules.columns:
        raise ValueError(
            f"sort_by='{sort_by}' is not in rules columns: {list(rules.columns)}"
        )

    top_rules = (
        rules.sort_values(sort_by, ascending=ascending)
        .head(top_k)
        .reset_index(drop=True)
    )

    # 7) pivot (기본은 lift)
    value_col = sort_by if sort_by in rules.columns else "lift"
    pivot_data = top_rules.pivot_table(
        index="antecedents_str",
        columns="consequents_str",
        values=value_col,
        fill_value=0,
        aggfunc="max",
    )

    # (선택) 컬럼 순서를 보기 좋게 정렬
    pivot_data = pivot_data.reindex(sorted(pivot_data.columns), axis=1)

    return {
        "rules": rules,
        "top_rules": top_rules[
            ["antecedents_str", "consequents_str", "support", "confidence", "lift"]
            + [c for c in [sort_by] if c not in ("support", "confidence", "lift")]
        ],
        "pivot_data": pivot_data,
        "frequent_itemsets": frequent_itemsets,
    }


# def maket_besket(texts):
#     kiwi = Kiwi()

#     # STOP_NOUN = {"전북","전주","익산","군산","완주","김제"}  # 너무 흔하면 제외(선택)
#     STOP_NOUN = [
#         "그럼",
#         "그런",
#         "근데",
#         "그런데",
#         "이런",
#         "저런",
#         "것",
#         "수",
#         "등",
#         "좀",
#         "진짜",
#         "ㅋㅋ",
#         "ㅋㅋㅋ",
#         "ㅋㅋㅋㅋ",
#         "ㅎㅎ",
#         "ㅎㅎㅎ",
#         "아냐",
#         "아니",
#         "뭐",
#         "왜",
#         "하고",
#         "하는",
#         "하다",
#         "됐다",
#         "되다",
#         "있다",
#         "없다",
#         "때",
#         "때문",
#         "이유",
#         "전주",
#         "익산",  # <- 특정 단어가 너무 흔해서 규칙을 망치면 넣어도 됨(선택)
#     ]

#     def nouns_kiwi(text: str) -> list[str]:
#         text = _clean_ko(text)
#         tokens = kiwi.tokenize(text)
#         nouns = [t.form for t in tokens if t.tag.startswith("NN")]  # 명사류
#         nouns = [n for n in nouns if len(n) >= 2 and n not in STOP_NOUN]
#         return nouns

#     items_list = [nouns_kiwi(t) for t in texts]

#     te = TransactionEncoder()
#     te_arr = te.fit(items_list).transform(items_list)

#     df = pd.DataFrame(te_arr, columns=te.columns_)

#     frequent_itemsets = apriori(df, min_support=0.02, use_colnames=True, max_len=2)

#     rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)

#     pivot_data = (
#         rules.sort_values("lift", ascending=False)
#         .head(20)
#         .pivot_table(
#             index="antecedents",  # 행
#             columns="consequents",  # 열
#             values="lift",  # 기준
#             fill_value=0,  # 매칭되지 않는 것은 이걸로 채워라.
#         )
#     )

#     return {"pivot_data": pivot_data, "rules": rules}


# def _clean_ko(s: str) -> str:
#     s = s.lower()
#     s = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", s)  # 특수문자 제거
#     s = re.sub(r"\s+", " ", s).strip()
#     return s
