# 全国番付の公開（GitHub Actions が 10 分おきに実行）。board.txt を作って GitHub Pages に置く。
# board.txt: 1 行目 "#updated<TAB>時刻（日本時間）"、2 行目から "順位<TAB>名前<TAB>スコア"。ワールド（NagesenGlobalBoard）が読む。
#
# 取り方は 2 通り。設定値はどちらも GitHub の Settings → Secrets and variables → Actions → *Secrets* に入れて
# ワークフローの env で渡す（公開リポジトリの Actions のログは誰でも読めるので、Variables ではなく Secrets）。
#   1) BOARD_URL … 中継（Cloudflare Workers）の /board を取るだけ。**こちらが本命**。
#      PlayFab のタイトル ID も秘密鍵も GitHub 側に置かずに済む。中継に秘密鍵を入れてデプロイしたらこちらへ移る。
#   2) TITLE_ID + STAT_NAME … PlayFab を直接読む（中継を秘密鍵対応にするまでの繋ぎ）。
import os, json, urllib.request, urllib.error, datetime

URL = os.environ.get("BOARD_URL", "")
TITLE = os.environ.get("TITLE_ID", "")
STAT = os.environ.get("STAT_NAME", "")


def from_relay(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nagesen-board"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    if not body.startswith("#updated"):
        raise SystemExit("board error: unexpected body")
    return body


def from_playfab(title, stat):
    base = f"https://{title}.playfabapi.com"

    def call(path, body, ticket=None):
        head = {"Content-Type": "application/json"}
        if ticket:
            head["X-Authorization"] = ticket
        req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST", headers=head)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["data"]

    ticket = call("/Client/LoginWithCustomID", {"TitleId": title, "CustomId": "board-reader", "CreateAccount": True})["SessionTicket"]
    try:
        rows = call("/Client/GetLeaderboard", {"StatisticName": stat, "StartPosition": 0, "MaxResultsCount": 100}, ticket)["Leaderboard"]
    except urllib.error.HTTPError as e:   # まだ誰も記録していない（統計が無い）ときは空の番付
        print("leaderboard error:", e.code)   # 本文は出さない（ログにタイトル ID を混ぜない）
        rows = []
    jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    lines = ["#updated\t" + jst]
    for r in rows:
        if r.get("StatValue", 0) <= 0:
            continue
        # PlayFab の表示名はクライアント API で誰でも書き換えられる。ワールドは TextMeshPro の
        # リッチテキストで描くので、山かっこを落とさないと全員の掲示板を壊せる。長さも切る
        name = (r.get("DisplayName") or "名無し")
        for bad in ("\t", "\n", "<", ">"):
            name = name.replace(bad, " " if bad in ("\t", "\n") else "")
        lines.append(str(r["Position"] + 1) + "\t" + name[:24] + "\t" + str(r["StatValue"]))
    return "\n".join(lines) + "\n"


if URL:
    try:
        body = from_relay(URL)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"board error: {e.code}")   # URL は出さない（ログに中継のアドレスを残さない）
    except SystemExit:
        raise
    except Exception:
        raise SystemExit("board error: unreachable")
elif TITLE and STAT:
    body = from_playfab(TITLE, STAT)
else:
    raise SystemExit("BOARD_URL か TITLE_ID+STAT_NAME が無い。GitHub の Actions Secrets に入れて env で渡すこと")

old = open("board.txt", encoding="utf-8").read() if os.path.exists("board.txt") else ""
# 順位が変わったときだけ書き換える（時刻だけの差分でコミットしない）
if old.split("\n", 1)[-1] != body.split("\n", 1)[-1] or not old:
    open("board.txt", "w", encoding="utf-8", newline="\n").write(body)
    print("updated", len(body.strip().split("\n")) - 1, "rows")
else:
    print("no change")
