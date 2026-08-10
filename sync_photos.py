# -*- coding: utf-8 -*-
"""
photos/ 폴더의 사진을 웹용으로 줄이고, 번호를 다시 매기고,
activities.html 의 장수를 맞춰 준다.

폴더 구조
    photos/<연도>/<반기>/<활동폴더>/01.jpg, 02.jpg ...
                                  /thumb.jpg       (선택, 목록 썸네일 · 3:2 권장)
                                  /poster.jpg      (선택, 포스터)
                                  /notice/01.jpg   (선택, 공지에 쓴 카드뉴스)

    반기는 h1(상반기) / h2(하반기).  예)  photos/2026/h1/0402-mapo/

쓰는 법
    사진을 넣거나 지운 뒤 실행하면 된다.

        python sync_photos.py

    하는 일
      1) 긴 변이 1400px 를 넘는 사진을 줄이고 JPEG 로 다시 저장한다.
         이미 작은 사진은 손대지 않으므로, 여러 번 실행해도 화질이 나빠지지 않는다.
      2) 남은 사진을 01.jpg, 02.jpg ... 로 다시 번호 매긴다.
      3) activities.html 의 seq(..., N) 숫자를 실제 장수에 맞춘다.

activities.html 은 어디까지 자동인가
      · 이미 있는 활동에 사진만 넣고 빼면  →  장수까지 전부 자동
      · 새 활동 폴더를 만들었으면          →  TERMS 에 항목을 직접 써야 한다
        (날짜·제목·아이콘 같은 건 폴더만 봐서는 알 수 없다)
        어느 쪽인지 실행 결과 맨 아래에 알려 준다.

사진을 지우기만 하고 이 스크립트를 돌리지 않아도 화면은 깨지지 않는다.
없는 사진은 갤러리에서 조용히 빠진다. 다만 목록의 "N장" 숫자만 실제와
달라지므로, 정확히 맞추고 싶을 때 실행하면 된다.
"""
import re
import sys
from pathlib import Path

try:                                  # 윈도우 콘솔에서 한글이 깨지지 않도록
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow 가 필요합니다:  python -m pip install Pillow")

BASE = Path(__file__).resolve().parent
PHOTOS = BASE / "photos"
HTML = BASE / "activities.html"

EXTS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
KEEP = {"poster", "thumb"}            # 사진이 아니라 따로 쓰이는 파일
MAX_EDGE = 1400                       # 긴 변 기준 최대 픽셀
QUALITY = 80

YEAR_RE = re.compile(r"^\d{4}$")
HALF_RE = re.compile(r"^h[12]$")

saved_before = saved_after = 0        # 압축으로 줄인 용량 집계
shrunk = 0


def needs_shrink(path: Path) -> bool:
    """줄일 필요가 있는지. 이미 규격에 맞는 JPEG 은 건드리지 않는다.
       (매번 다시 저장하면 화질이 조금씩 나빠지므로)"""
    if path.suffix.lower() not in (".jpg", ".jpeg"):
        return True                   # PNG 등은 JPEG 으로 바꾼다
    try:
        with Image.open(path) as im:
            return max(im.size) > MAX_EDGE
    except Exception:
        return False


def write_web(src: Path, dst: Path):
    """웹용으로 줄여서 저장한다."""
    global saved_before, saved_after, shrunk
    before = src.stat().st_size
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    if src != dst and src.exists():
        src.unlink()
    saved_before += before
    saved_after += dst.stat().st_size
    shrunk += 1


def sort_key(p: Path):
    """번호가 붙은 사진은 숫자 순서로, 새로 넣은 파일은 그 뒤에 이름순으로.

       사전순으로 두면 100.jpg 가 11.jpg 보다 앞에 와서, 100장이 넘는 순간
       실행할 때마다 사진 순서가 뒤섞인다."""
    if p.stem.isdigit():
        return (0, int(p.stem), "")
    return (1, 0, p.name.lower())


def tidy(folder: Path) -> int:
    """폴더 안 사진을 웹용으로 줄이고 01.jpg 부터 번호를 다시 매긴다."""
    shots = sorted((p for p in folder.iterdir()
                    if p.is_file() and p.suffix in EXTS and p.stem not in KEEP),
                   key=sort_key)

    # 이름이 겹치지 않게 임시 이름을 한 번 거친다
    tmp = []
    for i, p in enumerate(shots, 1):
        t = folder / f"__{i:03d}.tmp"
        p.rename(t)
        tmp.append((t, p.suffix))

    for i, (t, suffix) in enumerate(tmp, 1):
        dst = folder / f"{i:02d}.jpg"
        probe = t.with_suffix(suffix)          # 확장자를 되살려 판단
        t.rename(probe)
        if needs_shrink(probe):
            write_web(probe, dst)
        else:
            probe.rename(dst)

    # 썸네일·포스터도 규격을 넘으면 줄인다 (이름은 그대로)
    for special in KEEP:
        f = folder / f"{special}.jpg"
        if f.exists() and needs_shrink(f):
            write_web(f, f)

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
                extra = []
                if (folder / "thumb.jpg").exists():
                    extra.append("썸네일")
                if (folder / "poster.jpg").exists():
                    extra.append("포스터")
                print(f"  {folder.name:22s} {counts[key]:3d}장  {' '.join(extra)}")

                notice = folder / "notice"
                if notice.is_dir():
                    counts[key + "/notice"] = tidy(notice)
                    print(f"  {'└ notice':22s} {counts[key + '/notice']:3d}장  (참고)")
            print()

    if shrunk:
        print(f"압축: {shrunk}장  "
              f"{saved_before/1024/1024:.1f}MB → {saved_after/1024/1024:.1f}MB")
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

    activities = [k for k in counts if not k.endswith("/notice")]
    print(f"완료 - 활동 {len(activities)}개, "
          f"사진 {sum(counts[k] for k in activities)}장, 장수 갱신 {len(changed)}건")

    # ── activities.html 과 폴더가 어긋나는 곳 알려주기 ──
    referenced = {m.group(1) for m in re.finditer(r"seq\('(photos/[^']+)'", html)}

    orphans = sorted(k for k in activities if k not in referenced)
    if orphans:
        print()
        print("폴더는 있는데 activities.html 에 항목이 없습니다.")
        print("TERMS 에 아래 활동을 직접 추가해 주세요 (날짜·제목·아이콘 등):")
        for o in orphans:
            year, half, name = o.split("/")[1:4]
            print(f"    {o}   ({counts[o]}장)")
            print(f"      → year: {year}, half: {half[1]} 항목 안에")
            print(f"         photos: seq('{o}', {counts[o]})")

    ghosts = sorted(p for p in referenced if p not in counts and "<" not in p)
    if ghosts:
        print()
        print("activities.html 이 참조하지만 폴더가 없습니다 (오타이거나 아직 안 만든 폴더):")
        for g in ghosts:
            print("  ", g)


if __name__ == "__main__":
    main()
