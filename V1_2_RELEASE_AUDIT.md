# 下3トレーナー v1.2 release audit

Date: 2026-10-08

## Result

**PASS**

## Inventory

- R7 / 令和7年度 第51回: 60問
- R6 / 令和6年度 第50回: 60問
- R3 / 令和3年度 第47回: 60問
- Total: **180問**

## R3 source contract

### Problem text
第47回（令和3年度）の実問題が保存されているページを本文ソースとして使用。

- https://ameblo.jp/gensan2155/entry-12767988422.html

問題文・選択肢は、学習画面向けに空白・改行・全半角を読みやすく整形した。
似た問題や生成問題への置換は行っていない。

### Answer key
本文保存ページとは別系統の第47回答え表で問1〜60を照合。

- https://gesuidou.link/gesan47/

Result:
- answers checked: 60 / 60
- mismatches: 0

日本下水道事業団の現存資料でも、第47回第3種が60問・合格基準43点であったことを確認。

- https://www.jswa.go.jp/company/shuupan/mizusumashi/pdf/187.pdf

## Automated audit

GitHub Actions: **Build and validate study site**

2026-10-08 v1.2 build result:

```
question_counts:
  R7: 60
  R6: 60
  R3: 60
  total: 180

VALIDATION PASS:
v1.2, 180 questions,
identity/answer keys checked,
R3 stems/choices checked,
one-question views R7 60/60 + R6 60/60
```

Additional checks:
- R7 official PDF question-header detection: 60 / 60
- R7 four-choice marker check: 60 / 60
- R6 one-question views: 60 / 60
- R3 IDs: R3-01 ... R3-60
- R3 question numbers: 1 ... 60, no gaps
- R3 stems: 60 / 60 non-empty
- R3 choices: 4 × 60
- R3 answers: 60 / 60 canonical-key match
- Duplicate IDs across 180 questions: 0
- JavaScript syntax: PASS
- GitHub Pages deployment: PASS

## Caveat

R7は現在入手できる日本下水道事業団公式問題PDFを直接正本としている。

R6・R3は公式サイトで当該年度の問題PDF掲載が終了しているため、保存資料を本文ソースとしている。
したがってR3について「現在のJS公式PDFとのバイト単位一致」とは表現しない。

一方で、R3は実問題保存本文と別系統の正答表を分離して確認し、
教材内の問番号・4選択肢・正答対応を60問すべて自動検査している。

## Final status

**v1.2 / 180 questions / release ready**
