# deck-portfolio-studio

마케팅 **발표덱**과 **개인 포트폴리오 자산**을 검증된 디자인 시스템으로 빠르게 만들어 주는 Claude Code 플러그인.
면접 발표덱 15건 이상에서 반복 검증된 워크플로우를 표준화했습니다. (원작: 이도형 / Covering)

## 무엇이 들어있나

| 구성 | 역할 |
|------|------|
| `/interview-deck` 스킬 | 면접 발표덱 6단계 파이프라인 (인테이크→병렬 리서치→서사→캡처→빌드→배포→회고) |
| `/brand-accelerator` 스킬 | 개인 포트폴리오 브랜드 자산(덱·웹·캐러셀·이력서) 제작 **템플릿**. 본인 프로필/성과를 채워 사용 |
| `/speech-style` 스킬 | 그로스 마케터 Slack/포트폴리오 **말투 톤**(협업·서사·분석 메모 3모드) |
| `slide-architecture.md` | 검증된 13p 서사 레시피 + HTML 컴포넌트 카탈로그 |
| `deck-template.html` | 1280×720 키보드 네비 단일 HTML 덱 스캐폴드 (브랜드 톤만 교체) |
| `deck-researcher` 에이전트 | 회사·JD·경쟁사·시장·벤치마크를 facet별 **병렬 리서치** (출처·신뢰도 태그) |
| `deck-deployer` 에이전트 | 완성 덱을 **본인 GitHub Pages**에 배포·200 검증 (최초 1회 환경 설정 필요) |

## 설치

```
/plugin marketplace add byuel0915-pixel/byuel_marketing
/plugin install deck-portfolio-studio@byuel-marketing
```

설치 후 `/help`에서 `/interview-deck`, `/brand-accelerator`, `/speech-style`가 보이면 완료입니다.

## 사용

- **면접 발표덱:** `/interview-deck` 또는 `"OO 회사 OO 직무 면접 발표덱 만들어줘"` → 회사·채용공고 URL·면접 단계·발표자 이름을 물어본 뒤 자동 진행.
- **개인 포트폴리오:** `/brand-accelerator` → 무엇을(덱·웹·캐러셀·이력서) 만들지 + 본인 프로필/성과 데이터를 한 번 받아 일관된 디자인으로 생성.
- **말투 톤:** `/speech-style` → 협업 메시지(A) / 포트폴리오 서사(B) / 분석 메모(C) 중 모드 선택.

## 최초 1회 설정 — 배포(deck-deployer)

`deck-deployer`는 **사용자마다 환경이 달라** 처음 쓸 때 아래를 한 번 물어봅니다(또는 직접 알려주세요):

- **Pages repo 로컬 경로** — 예: `C:\Users\<id>\pages`
- **원격 repo URL** — 예: `https://github.com/<user>/<user>.github.io`
- **라이브 URL 규칙** — `https://<user>.github.io/<프로젝트명>/`
- **git 실행 경로** — PATH에 없으면 풀패스(예: `C:\Program Files\Git\cmd\git.exe`)
- **인증** — git credential manager나 SSH 키가 이미 설정돼 있어야 함

> 배포가 필요 없으면 빌드된 HTML을 로컬에서 그대로 열어 발표해도 됩니다.

## 권장 환경
- **Playwright MCP** — 경쟁사/벤치마크 화면 실측 캡처용. 없으면 캡처 단계는 건너뛰고 수동 첨부.
- **WebSearch / WebFetch** — 리서치용(기본 제공).
- **GitHub Pages repo + git** — 배포를 쓸 경우만.

## 주의 (꼭 읽어주세요)
- 모든 외부 수치에는 **출처·신뢰도 태그**를 답니다. 추측으로 빈칸을 메우지 않습니다.
- `/brand-accelerator`의 프로필 양식에 들어가는 **개인 연락처·회사 내부 매출 수치**는 공개 repo/사이트에 그대로 올리지 마세요. 외부 공개용이면 성장률(%)·상대값으로 바꾸거나 비공개 처리하세요.
- 회사 **내부데이터가 포함된 덱**은 public repo에 배포하지 마세요. (deck-deployer가 경고합니다.)

## 라이선스/출처
원작 워크플로우·디자인 시스템: 이도형(Covering). 개인 정보·내부 수치는 템플릿 플레이스홀더로 치환되어 있으며, 사용자가 본인 데이터로 채워 사용합니다.
