# 알바트로스냅 웹사이트

서강대학교 AIㆍSW 대학원 사진 동아리 소개 · 활동 기록 페이지.

- 모집 페이지 — `index.html`
- 활동 기록 — `activities.html`
- 배포 — https://dahyun-han.github.io/albatrosnap/ (master 에 푸시하면 1~2분 뒤 반영)

---

## 자주 하는 일

명령은 모두 `웹 사이트` 폴더에서 실행합니다.
파이썬은 반드시 `env\Scripts\python.exe` 를 쓰세요. 전역 python 에는 Pillow 가 없습니다.

### 1. 기존 활동에 사진을 넣거나 뺄 때

사진을 폴더에 넣거나 지운 다음:

```
env\Scripts\python.exe sync_photos.py
```

끝입니다. 장수까지 자동으로 맞춰집니다.

### 2. 새 활동을 추가할 때

**① 사진 폴더 만들기**

```
photos\<연도>\<반기>\<폴더이름>\
```

반기는 `h1`(1~6월) / `h2`(7~12월). 폴더 이름은 `0913-namsan` 처럼 날짜+장소를 권장합니다.

| 파일 | 필수 | 설명 |
|---|---|---|
| 사진 여러 장 | ○ | 파일명은 아무거나. 스크립트가 `01.jpg` 부터 다시 매깁니다 |
| `thumb.jpg` | – | 목록 카드에 쓸 대표 사진. **3:2 비율** 권장 (1008×672) |
| `poster.jpg` | – | 홍보 포스터. 상세 화면 왼쪽에 크게 들어갑니다 |
| `notice\` | – | 공지에 썼던 카드뉴스. 상세의 '참고' 칸에 순서대로 |

`thumb.jpg` 가 없으면 포스터를, 그것도 없으면 첫 번째 사진을 대표로 씁니다.

**② `activities.txt` 에 블록 추가** — 기존 내용은 그대로 두고 아래를 덧붙입니다.

```
---

날짜: 2026-09-13
제목: 남산 출사
부제: 가을 야경 담기
장소: 남산공원
시간: 오후 5시
아이콘: camera
폴더: 0913-namsan
설명: 첫 줄입니다.
  들여쓰면 화면에서도 줄이 나뉩니다.
```

필수는 **날짜 · 제목 · 폴더** 셋뿐입니다. 나머지 줄은 없으면 지우세요.
순서는 상관없습니다 — 화면에는 날짜순으로 정렬됩니다.

**③ 두 스크립트 실행**

```
env\Scripts\python.exe sync_photos.py
env\Scripts\python.exe build_activities.py
```

**④ 배포**

```
git add -A
git commit -m "남산 출사 추가"
git push
```

### 3. 아직 안 다녀온 활동을 미리 올릴 때

블록에 `예정: y` 한 줄을 넣으면 '예정' 표시가 붙습니다.
다녀온 뒤 그 줄만 지우고 다시 빌드하면 됩니다.

### 4. 새 아이콘을 추가할 때

원본을 `아이콘\` 에 한글 이름으로 두고, `icons\` 에 **영문 이름으로 복사**합니다.
GitHub Pages 에서 한글 경로가 문제를 일으킬 수 있어 웹에서는 영문 사본만 씁니다.

---

## 스크립트

### `sync_photos.py` — 사진 정리

- 긴 변이 **1400px** 를 넘는 사진을 줄이고 JPEG 로 저장 (품질 80)
- 남은 사진을 `01.jpg` 부터 다시 번호 매김
- `activities.html` 의 장수 갱신
- 폴더는 있는데 `activities.txt` 에 없는 활동을 알려줌

이미 규격에 맞는 사진은 건드리지 않습니다. 여러 번 실행해도 화질이 나빠지지 않습니다.

### `build_activities.py` — 활동 데이터 생성

`activities.txt` → `activities.html` 의 `/* TERMS:START */ ~ /* TERMS:END */` 사이를 다시 씁니다.

```
env\Scripts\python.exe build_activities.py --check
```

`--check` 를 붙이면 파일을 고치지 않고 확인만 합니다.
잘못 적은 곳이 있으면 한 번에 모아서 알려주고, 하나라도 있으면 파일을 건드리지 않습니다.

---

## 손대면 안 되는 곳

`activities.html` 의 아래 구간은 **자동 생성 영역**입니다. 직접 고치면 다음 빌드 때 지워집니다.

```js
/* TERMS:START */
const TERMS = [ ... ];
/* TERMS:END */
```

내용은 `activities.txt` 에서 고치세요. 그 바깥의 디자인·동작 코드는 직접 고쳐도 됩니다.

---

## 폴더 구조

```
웹 사이트\
  index.html           모집 페이지 (7장짜리 슬라이드)
  activities.html      활동 기록
  activities.txt       활동 데이터 ← 여기를 고칩니다
  sync_photos.py       사진 정리
  build_activities.py  활동 데이터 → HTML
  og.jpg               카카오톡·SNS 링크 미리보기 이미지
  icon2.ico            파비콘
  icons\               웹용 아이콘 (영문 이름)
  아이콘\               아이콘 원본 (한글 이름)
  photos\
    2026\
      h1\              상반기
        0402-mapo\
          01.jpg ...
          thumb.jpg
          poster.jpg
          notice\
      h2\              하반기
  env\                 파이썬 가상환경 (git 에 올라가지 않음)
```

원본 사진은 저장소에 넣지 않습니다. `대학원\동아리\활동\` 에 따로 보관합니다.

---

## 알아두면 좋은 것

- **활동 기록 첫 화면** — 달에 따라 먼저 열리는 반기가 바뀝니다.
  3~8월은 상반기, 9~2월은 하반기. `activities.html` 의
  `HALF1_FROM_MONTH` / `HALF2_FROM_MONTH` 숫자로 조절합니다.
  고른 반기가 비어 있으면 반대쪽을 엽니다.
- **카카오톡 미리보기** — og 태그를 고친 뒤에는
  [카카오 디버거](https://developers.kakao.com/tool/debugger/sharing) 에서 캐시를 초기화해야 반영됩니다.
- **사진 저장 억제** — 꾹 누르기·우클릭·드래그를 막아 뒀습니다.
  다만 주소를 직접 열거나 화면을 캡처하는 것까지는 막을 수 없습니다.
- **커밋하면 되돌리기 어렵습니다** — 사진은 한 번 푸시하면 git 기록에 남습니다.
  뺄 사진은 커밋 전에 지우세요.
