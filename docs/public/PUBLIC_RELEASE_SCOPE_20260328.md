# Public Release Scope

作成日: 2026-03-28

## 1. 目的

この文書は、GitHub 公開版として何を残し、何を出さないかを固定するためのスコープ定義です。

最上位目標は `GITHUB_PUBLIC_RELEASE_GOAL_20260328.md` とし、
この文書は実作業に落とした公開範囲の台帳として扱います。

## 2. 公開版の作業先

- 公開用ワークスペース:
  - `D:\github_public\masao-pipeline-public`

この作業先は本番とは分離し、コピー先として使います。

## 3. 公開版の主メッセージ

GitHub 公開版で一番伝えることは次です。

- 低スペック環境でも動く
- file-based state で追える
- queue で責務を分離している
- immutable な session 構造で壊れにくい
- rabbit video pipeline を例にした実運用設計である

つまり、コードの完全公開ではなく、
「壊れにくく、再実行しやすい自動処理パイプラインの設計思想」を見せることが主目的です。

## 4. 今回の公開版に含めるもの

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PUBLIC_SCOPE.md`
- `AGENTS.md`
- `.gitignore`
- `config/config.example.json`
- sample session の簡易構造
- sample `candidates_20s.jsonl`
- sample `decision.json`
- sample queue files
- 最小スクリプト
  - candidates を event queue に昇格するだけのサンプル

## 5. 今回の公開版に含めないもの

- API key
- token
- `.env.win`
- 実運用 prompt
- 実運用 API script
- render 完成版
- upload 完成版
- title / selection / threshold の完全ロジック
- playlist / auth / 投稿先情報
- `E:\masaos_mov` の実データ
- `keys` `prompts` `bgm` `models` の本番資産
- `work` の post-publish 実務コード

## 6. source -> public の対応

### current shorts line

- source:
  - `D:\OBS\REC\scripts\youtube\yolo\WIN`
- public:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `config/config.example.json`
  - `examples/*`
  - `scripts/build_event_queue.py`

### post-publish line

- source:
  - `D:\OBS\REC\work`
- public:
  - 初版では説明のみ
  - 実コードは出さない

### warehouse

- source:
  - `E:\masaos_mov`
- public:
  - `examples/session_sample`

### shared assets

- source:
  - `keys`
  - `prompts`
  - `bgm`
  - `models`
- public:
  - 実体は出さない
  - README と config example で参照概念のみ示す

## 7. 初版の完成条件

- `README.md` だけで全体像が分かる
- 初見の人が queue と state の役割を理解できる
- sample JSONL を見ればファイル契約が分かる
- 最小スクリプトを動かすと queue が 1 本生成される
- 機密、本番依存、核心ロジックが入っていない

## 8. 次の実作業

1. README を磨く
2. 公開版のディレクトリを調整する
3. sample data を必要最小限で揃える
4. 最小スクリプトを検証する
5. 公開前チェックリストを作る
