# -*- coding: utf-8 -*-
"""
photos/ 폴더의 사진을 정리하고 activities.html 의 장수를 맞춰 준다.

폴더 구조
    photos/<연도>/<반기>/<활동폴더>/01.jpg, 02.jpg ...
                                  /poster.jpg      (선택, 포스터)
                                  /notice/01.jpg   (선택, 공지에 쓴 카드뉴스)

    반기는 h1(상반기) / h2(하반기).  예)  photos/2026/h1/0402-mapo/

쓰는 법
  1) 빼고 싶은 사진은 그냥 지운다. 새로 넣을 때 파일명은 아무거나 상관없다.
  2) 이 파일을 실행한다.
        python sync_photos.py
  3) 남은 사진이 01.jpg, 02.jpg ... 로 다시 번호가 매겨지고,
     activities.html 의 seq(..., N) 숫자도 자동으로 맞춰진다.

사진을 지우기만 하고 이 스크립트를 돌리지 않아도 화면은 깨지지 않는다.
없는 사진은 갤러리에서 조용히 빠진다. 다만 목록의 "N장" 숫자만 실제와
달라지므로, 정확히 맞추고 싶을 때 실행하면 된다.

새 반기를 시작할 때
  photos/2027/h1/ 폴더를 만들고 그 안에 활동 폴더를 넣은 뒤,
  activities.html 의 TERMS 에 { year: 2027, half: 1, activities: [...] } 를 추가한다.
"""
import re
import sys
from pathlib import Path

try:                                  # 윈도우 콘솔에서 한글이 깨지지 않도록
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = Path(__file__).resolve().parent
PHOTOS = BASE / "photos"
HTML = BASE / "activities.html"
EXTS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

YEAR_RE = re.compile(r"^\d{4}$")
HALF_RE = re.compile(r"^h[12]$")


def tidy(folder: Path) -> int:
    """폴더 안 사진을 01.jpg 부터 다시 번호 매기고, 장수를 돌려준다."""
    shots = sorted(p for p in folder.iterdir()
                   if p.is_file() and p.suffix in EXTS and p.stem != "poster")
    tmp = []
    for i, p in enumerate(shots, 1):
        t = folder / f"__{i:03d}.tmp"
        p.rename(t)
        tmp.append(t)
    for i, t in enumerate(tmp, 1):
        t.rename(folder / f"{i:02d}.jpg")
    return len(tmp)


def main():
    if not PHOTOS.exists():
        sys.exit(f"photos 폴더가 없습니다: {PHOTOS}")

    counts = {}
    skipped = []

    for year in sorted(PHOTOS.iterdir()):
        if not year.is_dir():
            continue
        if not YEAR_RE.match(year.name):
            skipped.append(year.name)
            continue

        for half in sorted(year.iterdir()):
            if not half.is_dir():
                continue
            if not HALF_RE.match(half.name):
                skipped.append(f"{year.name}/{half.name}")
                continue

            tag = "상반기" if half.name == "h1" else "하반기"
            print(f"[{year.name} {tag}]")

            for folder in sorted(half.iterdir()):
                if not folder.is_dir():
                    continue
                key = f"photos/{year.name}/{half.name}/{folder.name}"
                counts[key] = tidy(folder)
                poster = "포스터 O" if (folder / "poster.jpg").exists() else "       "
                print(f"  {folder.name:22s} {counts[key]:3d}장  {poster}")

                # 공지에 썼던 카드뉴스는 활동폴더/notice/ 안에 따로 둔다
                notice = folder / "notice"
                if notice.is_dir():
                    counts[key + "/notice"] = tidy(notice)
                    print(f"  {'└ notice':22s} {counts[key + '/notice']:3d}장  (참고)")
            print()

    if skipped:
        print("건너뜀 (연도/반기 이름 형식이 아님):", ", ".join(skipped))
        print("  연도는 4자리 숫자, 반기는 h1 또는 h2 여야 합니다.")
        print()

    if not counts:
        sys.exit("정리할 활동 폴더를 찾지 못했습니다.")

    if not HTML.exists():
        sys.exit(f"{HTML.name} 을 찾을 수 없어 장수는 갱신하지 못했습니다.")

    html = HTML.read_text(encoding="utf-8")
    changed = []

    def repl(m):
        path, old = m.group(1), int(m.group(2))
        if path not in counts:          # 주석 속 예시 등은 건드리지 않는다
            return m.group(0)
        new = counts[path]
        if new != old:
            changed.append(f"{path}  {old}장 → {new}장")
        return f"seq('{path}', {new})"

    html = re.sub(r"seq\('([^']+)',\s*(\d+)\)", repl, html)
    HTML.write_text(html, encoding="utf-8")

    for line in changed:
        print("갱신:", line)

    total = sum(n for k, n in counts.items() if not k.endswith("/notice"))
    print(f"완료 - 활동 {len([k for k in counts if not k.endswith('/notice')])}개, "
          f"사진 {total}장, 장수 갱신 {len(changed)}건")

    # HTML 이 참조하지만 실제로는 없는 폴더 알려주기
    referenced = {m.group(1) for m in re.finditer(r"seq\('(photos/[^']+)'", html)}
    ghosts = sorted(p for p in referenced
                    if p not in counts and "<" not in p)   # 주석 속 예시는 제외
    if ghosts:
        print()
        print("HTML 이 참조하지만 폴더가 없습니다 (오타이거나 아직 안 만든 폴더):")
        for g in ghosts:
            print("  ", g)


if __name__ == "__main__":
    main()
