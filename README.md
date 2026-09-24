# Meong Meong!

白くふわふわした犬の「クルム」と同じ部屋で過ごす、PC向けの育成・コミュニケーションゲームです。ごはんや遊びを楽しめるほか、3種類のミニゲームで条件を満たすと、新しい遊びがサプライズで解放されます。

## 主な機能

- ユーザー登録、ログイン、初回ニックネーム設定、ログアウト
- クルムの部屋での「ごはん」と「あそぶ」
- 時間ベースのクルムの生活・リアクションアニメーション
- お散歩ジャンプ、吠えるタイピング、おやつキャッチ
- 共通結果画面、ユーザー別自己ベスト、初回限定アンロック演出
- 解放後のノーズワーク、ひっぱりっこ、ボール遊び
- SQLiteによるアカウント、自己ベスト、解放状態の保存

## 技術スタック

- Python 3.14.7
- pygame-ce 2.5.8
- SQLite（Python標準ライブラリ）
- pytest

## セットアップ（Windows / PowerShell）

プロジェクトのルートフォルダで、仮想環境を作成して依存パッケージをインストールします。PowerShellの実行ポリシーに左右されないよう、仮想環境内のPythonを直接呼び出します。

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## ゲームの起動

```powershell
.venv\Scripts\python.exe -m src.main
```

主な操作は画面内に表示されます。ミニゲーム中に `Esc` を押すと、途中終了の確認画面が開きます。途中終了した記録は保存されません。

## テスト

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

画面を開かず初期化とタイトル画面の描画だけを確認する場合は、次を使用します。

```powershell
.venv\Scripts\python.exe -m src.main --smoke-test
```

## プロジェクト構成

```text
Meong-Meong/
├─ assets/                 # 正式マスター画像、背景、UI用素材
├─ data/                   # タイピング単語と実行時SQLiteファイル
├─ docs/                   # 企画書・実装仕様書
├─ src/
│  ├─ minigames/           # 3種類のミニゲーム
│  ├─ screens/             # 認証・部屋・選択・結果・解放画面
│  ├─ auth_service.py      # パスワード検証・ハッシュ化
│  ├─ animation.py         # クルムの共通アニメーション状態管理
│  ├─ database_manager.py  # SQLiteの初期化と保存・読み込み
│  ├─ game_rules.py        # 得点、クリア、解放の固定ルール
│  ├─ sound_manager.py     # 効果音生成・再生・重複制御
│  ├─ config.py            # 固定仕様と調整可能なゲームバランス
│  └─ main.py              # 起動入口
├─ tests/                  # ルール、DB、全画面描画のテスト
├─ AGENTS.md
├─ README.md
└─ requirements.txt
```

## 保存データ

初回起動時に `data/meong_meong.db` が自動作成されます。`users` テーブルにはログイン情報とニックネーム、`user_progress` テーブルにはユーザーごとの自己ベストと解放状態を保存します。

パスワードはランダムなソルトを使ったPBKDF2-HMAC-SHA256でハッシュ化し、平文では保存しません。自己ベストは未プレイ時には `NULL` で、既存記録を上回った場合のみ更新されます。DBファイルは `.gitignore` の対象です。
