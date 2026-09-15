"""물길 외부 감시 (GitHub Actions에서 5분마다 실행, 2026-09-15).
fly 밖(GitHub)에서 /health·/health/db를 점검하고, 상태가 바뀔 때(다운·복구)만 텔레그램으로 알린다.
fly 자체 장애로 내부 감시기(mulgil-watchdog)까지 죽는 경우를 대비한 제3자 보험."""
import json, os, time, datetime, urllib.request, urllib.error

URLS = {"API": "https://mulnale-api.fly.dev/health", "DB": "https://mulnale-api.fly.dev/health/db"}
KST = datetime.timezone(datetime.timedelta(hours=9))


def probe(url: str) -> int:
    """200이 아니면 20초 뒤 1회 재시도 — 순간 흔들림으로 오경보 내지 않기."""
    code = 0
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "mulgil-uptime/1.0"}), timeout=20) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        if code == 200:
            return 200
        time.sleep(20)
    return code


state = json.load(open("state.json", encoding="utf-8")) if os.path.exists("state.json") else {}
now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
msgs = []
for name, url in URLS.items():
    code = probe(url)
    st = "up" if code == 200 else "down"
    prev = state.get(name, {}).get("state")
    if prev != st:
        if st == "down":
            msgs.append(f"[물길 외부감시-GitHub] {name} 응답 없음 (HTTP {code}, 2회 연속) {now}\n{url}\n내부 감시기 경보가 같이 안 왔다면 fly 전체 장애 가능성.")
        elif prev == "down":
            msgs.append(f"[물길 외부감시-GitHub] {name} 복구됨 {now} (다운 시작 {state[name].get('since', '?')})")
        else:
            msgs.append(f"[물길 외부감시-GitHub] 감시 시작 — {name} {st} {now}")
        state[name] = {"state": st, "since": now, "code": code}
    else:
        state[name].update(code=code, last=now)
    print(f"{name}: HTTP {code} → {st}")
state["_last_check"] = now

tok, chat = os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", "")
for m in msgs:
    print("알림:", m.replace("\n", " | "))
    if tok and chat:
        req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
                                     data=json.dumps({"chat_id": chat, "text": m}).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=15).read()
        except Exception as e:
            print("텔레그램 실패:", type(e).__name__)

# 상태 변화가 있으면 즉시, 없으면 하루 1회만 커밋(60일 무활동 시 스케줄이 꺼지므로 활동 유지)
today = now[:10]
if msgs or state.get("_heartbeat_date") != today:
    state["_heartbeat_date"] = today
    open("COMMIT", "w").write("1")
json.dump(state, open("state.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
