# v1.4 学習UI回帰テスト・問題原本調査（2026-10-08）

## 結論

**アプリ v1.4 は240問を維持したまま、反復学習と本番型模試の重大な不整合を修正した。**

GitHub Actions:
- https://github.com/inarivf/-gesuido3-study/actions/runs/37723327886
- 公開: https://github.com/inarivf/-gesuido3-study/actions/runs/37723388608

## 改修

- 同じ学習セッション中に前後へ移動しても、再選択による解答履歴の二重カウントを防止
- 過去履歴に正解記録があっても、解答前に正解の選択肢が緑色に表示されない
- 模試の回答中は正誤・解説を一切表示せず、最後の一括採点で初めて公開
- 模試中の選択変更を許可、途中採点・制限時間終了時に回答済み・正解・誤答・未回答を集計
- 回答履歴は模試終了の一回だけ更新。終了後の再採点による二重計上も防止
- 弱点評価の「覚えた（ok）」は明示的な弱点解除に優先させる
- 学習履歴のローカル保存キー `gesuido3_progress_v1` は据え置き

## 自動テスト

`scripts/test_trainer_ui.js` が実際に生成した `index.html` 内のJavaScriptをNode.js VMで実行し、以下4つを検査。

1. 1回の学習内で解答後に前後移動・再選択しても二重計上しない
2. 新規セッションで過去の正解が先に表示されない、弱点解除が正しく反映される
3. 模試中は正解を公開せず選択を変更できる。終了後は60問満点、誤答、未回答を採点し一回だけ履歴反映
4. 新規模試は未回答状態へ戻るが、過去の学習履歴は残る

結果:
```
VALIDATION PASS: v1.4, 240 questions
PASS: in-session review restores answer without double-counting
PASS: no historical answer leakage; explicit weak-point rating works
PASS: true deferred-feedback timed mock, review and single submission
PASS: new sessions retain history but do not leak answers
UI REGRESSION PASS: 4 scenarios
```

注：これはNode.js上でDOM操作を模倣する回帰検査であり、iPhone Safari実機での操作テストを代替するものではない。

## 追加の原問題調査：R4・R5

**追加収録0問、保留継続**。以下は状況の正本。

R4:
- JSWAの旧緊急案内ブログによると第48回の問題・正答は2022年11月16日から2023年1月16日まで公表。
  https://jstodakentei.livedoor.blog/archives/17671669.html
- 問題原本は現在の公式サイトでは確認できない。

R5:
- JSWAの2023年11月16日公表告知は残る。
  https://www.jswa.go.jp/kentei/pdf/annai/20231116oshirase.pdf
- 正答60問は保存済み。問16は選択肢に正解が存在せず全員1点。
- 問題原本60問を正当に取得・照合できず、収録保留。

別経路:
- 国立国会図書館 WARP がJSWA旧ウェブサイトの保存目録を保有：
  https://warp.ndl.go.jp/waid/10298
- ただし今回の検索環境では同アーカイブの実際の過去PDF取得は403で拒否され、R4/R5問1～60の原文は確認できない。**目録があることとPDF本文が保存されていることは別問題**。
- 出版社の市販書籍・アプリに両年の収録があるが、これだけでは本文を検証できず、第三者の著作物を自動転載する根拠にもならない。

## 次の受入れ条件

R4/R5の問題冊子PDF・鮮明なスキャン・信頼できるWeb保存原文を取得後、既存の `scripts/audit_pending_years.py` で60問/240択、正答、出典ハッシュ、図表、転記ミスを点検。
JSWA公式問題自体が入手できない場合は原本一致を断定しない。

## 公開影響

- 学習用240問は変更なし
- R7/R6/R3/R2の既存本文・正答データは変更なし
- 保存済み学習履歴のキーは変更なし
- v1.4公開済み、GitHub Actionsで生成・検査・公開成功
