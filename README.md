## unitypackage_opener

Windows のエクスプローラーから .unitypackage を右クリック解凍できる GUI ツールです。CustomTkinter によるダークテーマ、メイリオフォント対応。設定に応じて下記をサポートします。

- 解凍モード: マージ/個別
- 競合解決: 常に上書き/常にスキップ/常に名前を変えて保存/毎回質問
- 出力先フォルダの指定（自動=入力ファイルの場所／固定パス）

### 初回起動とレジストリ登録

生成した `unitypackage_opener.exe` を一度起動すると、現在の実行パスでエクスプローラーのコンテキストメニューへ登録します（起動パスが変わると自動再登録）。

登録先（HKCU）
- `Software\Classes\.unitypackage` → `Unitypackage`
- `Software\Classes\Unitypackage\shell\Extract with unitypackage_opener`（複数選択は1プロセスに集約）
- `Software\Classes\Unitypackage\shell\Open unitypackage_opener (GUI)`（設定画面を開く）

### 使い方

1. `unitypackage_opener.exe` を直接起動（または右クリック →「Open unitypackage_opener (GUI)」）し、GUIで設定を保存します。
2. エクスプローラーで .unitypackage を1つまたは複数選択し、右クリック →「Extract with unitypackage_opener」を選択します。
		- この経路では GUI は原則表示されず、保存済み設定に従って自動解凍されます（ヘッドレス実行）。
	- マージモードの場合、複数パッケージでも出力先は1つに統合されます。
		- 競合解決が「毎回質問」の場合、ヘッドレス実行でも最初の一度だけ小さなポップアップで確認し、以降は同じ選択を適用します。

GUIは設定画面のみになりました（解凍実行ボタンはありません）。

### ビルド

PyInstaller を使用します。

```
pyinstaller --onefile --noconsole -n unitypackage_opener unitypackage_opener\__main__.py
```

出力: `dist/unitypackage_opener.exe`

### 設定ファイル

`%USERPROFILE%/.unitypackage_opener/settings.json`

- mode: `merge` | `individual`
- conflict: `overwrite` | `skip` | `rename` | `ask`
- output_dir_mode: `auto` | `fixed`
- output_dir: 出力先フォルダ（fixed のときに使用）
- last_exe_path: 最終登録の実行ファイルパス
