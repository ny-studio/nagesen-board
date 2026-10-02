# 賽銭 VR 全国番付（公開用）

このリポジトリを GitHub に **公開** で作り、Settings → Pages で「Deploy from a branch / main / (root)」にする。
Actions が 10 分おきに PlayFab から順位を取り、`board.txt` を更新する（Actions タブで一度 `board` を手動実行すると確認できる）。

ワールドは `https://ny-studio.github.io/nagesen-board/board.txt` を読む（公開先: https://github.com/ny-studio/nagesen-board）。

## 秘密にするもの

このリポジトリは公開なので、**PlayFab のタイトル ID と統計名はファイルに書かない**。
Settings → Secrets and variables → Actions → **Secrets** に `TITLE_ID` と `STAT_NAME` を入れる（Variables ではなく Secrets。ログに出ても伏せられる）。
入れてからでないと `board` のワークフローは落ちる（board.txt は古いまま残るので、ワールドの表示は壊れない）。

タイトル ID は元のゲームのクライアントにも入っている値だが、ここに書くと解析なしで見つかる。クライアント API で統計を書ける設定のままだと、見つけた人が順位を書き換えられる（元のゲームの順位表も同じ）。
