# mulgil-uptime

물길(mulnale-api.fly.dev) 외부 감시. GitHub Actions가 5분마다 `/health`와 `/health/db`를 점검하고, 상태가 바뀔 때(다운·복구)만 텔레그램으로 알립니다.

- fly 내부 감시기(mulgil-watchdog)와 별개로, fly 전체 장애 때도 알리기 위한 제3자 보험입니다.
- 비밀은 저장소 Secrets(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)에만 있습니다. 코드에는 없습니다.
- `state.json`은 마지막 상태 기록입니다. 상태 변화 시 즉시, 평소엔 하루 1회 자동 커밋됩니다(60일 무활동 시 스케줄이 꺼지는 것을 막기 위함).
- 끄려면 Actions 탭에서 워크플로 "mulgil-uptime"을 Disable 하면 됩니다.
