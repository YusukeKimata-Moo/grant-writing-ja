# 申請書本文の機械チェック。checklist.md の★項目をこの出力で判定する。
# 使い方: python scripts/check_style.py <本文ファイル> [--limit 文字数制限]
# 出力は検出報告であり、最終判定(固有名詞の例外、根拠の有無など)はモデル/人間が行う。
import argparse
import re
from pathlib import Path

REDUNDANT = ["することができる", "を行う", "を実施する", "非常に", "極めて", "大いに"]
HEDGE_STACK = ["可能性が示唆され", "示唆されると考え", "と考えられる可能性"]
HOLLOW = ["重要であ", "注目され", "期待され", "革新的", "包括的", "飛躍的", "独創的", "画期的"]


def strip_ws(s):
    return re.sub(r"\s", "", s)


def find_lines(lines, word):
    return [i + 1 for i, line in enumerate(lines) if word in line]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--limit", type=int, help="文字数制限(空白・改行を除いて判定)")
    args = p.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")
    lines = text.splitlines()
    issues = 0

    n = len(strip_ws(text))
    print(f"文字数(空白・改行除く): {n}")
    if args.limit:
        pct = n / args.limit * 100
        mark = "OK" if 95 <= pct <= 100 else "NG"
        print(f"制限{args.limit}字に対して {pct:.1f}% (目標95〜100%) {mark}")
        if mark == "NG":
            issues += 1

    sents = [s.strip() for s in re.split(r"。", text) if strip_ws(s)]

    long_sents = [s for s in sents if len(strip_ws(s)) + 1 > 100]
    if long_sents:
        print(f"\n■ 100字超の文: {len(long_sents)}件 (多少の超過は許容)")
        for s in long_sents:
            print(f"  [{len(strip_ws(s)) + 1}字] {strip_ws(s)[:30]}…")
        issues += 1

    run_word, run_len = None, 0
    reported = set()
    for s in sents:
        end = strip_ws(s)[-2:]
        if end == run_word:
            run_len += 1
        else:
            run_word, run_len = end, 1
        if run_len >= 3 and end not in reported:
            print(f"\n■ 文末「〜{end}。」が3連続: …{strip_ws(s)[-15:]}。")
            reported.add(end)
            issues += 1

    kanji_runs = sorted(set(re.findall(r"[一-鿿々]{7,}", text)))
    if kanji_runs:
        print(f"\n■ 漢字7文字以上の連続 (固有名詞・専門用語は例外):")
        for w in kanji_runs:
            print(f"  {w}")

    for label, words in [("冗長表現(置換表)", REDUNDANT), ("留保の重ね掛け", HEDGE_STACK),
                         ("空洞語(根拠の有無を目視確認)", HOLLOW)]:
        hits = [(w, find_lines(lines, w)) for w in words if w in text]
        if hits:
            print(f"\n■ {label}:")
            for w, ls in hits:
                print(f"  「{w}」 {len(ls)}箇所 (行: {', '.join(map(str, ls[:5]))})")
            issues += 1

    if issues == 0 and not kanji_runs:
        print("\n機械チェック項目: 検出なし")


if __name__ == "__main__":
    main()
