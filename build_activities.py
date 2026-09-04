# -*- coding: utf-8 -*-
"""
activities.txt 를 읽어 activities.html 의 활동 데이터를 다시 만든다.

    python build_activities.py

activities.txt 에 활동 하나당 블록 하나를 쓰면 된다. 자세한 형식은 그 파일
맨 위 설명을 볼 것. 아래 것들은 적지 않아도 폴더를 보고 알아서 채운다.

    · 사진 장수
    · thumb.jpg / poster.jpg 유무
    · notice 폴더와 그 안의 장수
    · 연도와 상·하반기 (날짜에서 계산)

사진을 새로 넣었다면 sync_photos.py 를 먼저 돌려 번호와 크기를 정리한 뒤
이 스크립트를 실행하는 것이 좋다.

--check 를 붙이면 파일을 고치지 않고 확인만 한다.
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = Path(__file__).resolve().parent
DATA = BASE / "activities.txt"
HTML = BASE / "activities.html"
ICONS = BASE / "icons"
PHOTOS = BASE / "photos"

IMG_EXTS = {".jpg", ".jpeg", ".png"}   # 그 밖의 확장자는 원본으로 보고 알려 준다

START = "/* TERMS:START */"
END = "/* TERMS:END */"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEY_RE = re.compile(r"^([가-힣]+)\s*:\s*(.*)$")

# activities.txt 의 한글 키 → 내부 이름
KEYS = {
    "날짜": "date", "종료일": "endDate", "제목": "title", "부제": "subtitle",
    "장소": "place", "시간": "time", "인원": "people", "아이콘": "icon",
    "폴더": "folder", "설명": "desc", "예정": "upcoming", "메모": "note",
}

errors = []
warnings = []


def parse(text):
    """activities.txt → 활동 목록"""
    acts = []
    for bno, block in enumerate(text.split("\n---"), 1):
        lines = [l for l in block.split("\n") if not l.lstrip().startswith("#")]
        if not any(l.strip() for l in lines):
            continue

        item, last = {}, None
        for line in lines:
            if not line.strip():
                continue
            m = KEY_RE.match(line.strip())
            if m and m.group(1) in KEYS:
                last = KEYS[m.group(1)]
                item[last] = m.group(2).strip()
            elif m and not line.startswith(" "):
                errors.append(f"블록 {bno}: 모르는 항목 '{m.group(1)}'")
            elif last:
                # 이어지는 줄 — 설명은 줄바꿈으로, 나머지는 띄어쓰기로 잇는다
                sep = "<br>" if last == "desc" else " "
                item[last] = (item[last] + sep + line.strip()).strip(sep)
            else:
                errors.append(f"블록 {bno}: 항목 이름이 없는 줄 → {line.strip()!r}")
        item["_block"] = bno
        acts.append(item)
    return acts


def half_of(date):
    return 1 if int(date[5:7]) <= 6 else 2


def check(a):
    """빠진 것·틀린 것을 모아 둔다. 폴더에서 알아낼 수 있는 값도 채운다."""
    where = f"블록 {a['_block']}"
    title = a.get("title")
    if title:
        where += f" ({title})"

    # 서로 무관한 검사는 한 번에 모두 해서, 한 번 실행으로 다 고칠 수 있게 한다
    ok = True

    for need in ("date", "title", "folder"):
        if not a.get(need):
            ko = [k for k, v in KEYS.items() if v == need][0]
            errors.append(f"{where}: '{ko}' 가 없습니다")
            ok = False

    icon = a.get("icon") or "camera"
    if not (ICONS / f"{icon}.png").exists():
        errors.append(f"{where}: icons/{icon}.png 가 없습니다")

    if a.get("people") and not a["people"].isdigit():
        errors.append(f"{where}: 인원은 숫자만 적어주세요 → {a['people']}")

    if a.get("endDate"):
        if not DATE_RE.match(a["endDate"]):
            errors.append(f"{where}: 종료일은 2026-08-09 형식이어야 합니다 → {a['endDate']}")
            a.pop("endDate")
        elif a["endDate"] == a.get("date"):
            # 하루짜리 활동. 그대로 두면 '08.30 ~ 08.30' 으로 나온다
            a.pop("endDate")
        elif a["endDate"] < a.get("date", ""):
            errors.append(f"{where}: 종료일이 날짜보다 빠릅니다 → {a['date']} ~ {a['endDate']}")

    if a.get("date") and not DATE_RE.match(a["date"]):
        errors.append(f"{where}: 날짜는 2026-04-02 형식이어야 합니다 → {a['date']}")
        ok = False

    if not ok:
        return None

    year = int(a["date"][:4])
    half = half_of(a["date"])
    rel = f"photos/{year}/h{half}/{a['folder']}"
    folder = BASE / rel
    if not folder.is_dir():
        errors.append(f"{where}: 폴더가 없습니다 → {rel}")
        return None

    n = len([p for p in folder.iterdir()
             if p.is_file() and p.suffix.lower() == ".jpg" and p.stem.isdigit()])
    if n == 0 and not a.get("upcoming"):
        warnings.append(f"{where}: 사진이 한 장도 없습니다")

    def special(name):
        """thumb / poster 를 확장자 상관없이 찾는다. sync 전이면 알려 준다."""
        found = sorted(f for f in folder.glob(f"{name}.*")
                       if f.is_file() and f.suffix.lower() in IMG_EXTS)
        if not found:
            return None
        f = found[0]
        if f.suffix.lower() != ".jpg":
            warnings.append(f"{where}: {f.name} 은 JPEG 이 아닙니다 — "
                            f"sync_photos.py 를 먼저 실행하세요")
        return f"{rel}/{f.name}"

    strays = sorted({p.suffix.lower() for p in folder.iterdir()
                     if p.is_file() and p.suffix.lower() not in IMG_EXTS})
    if strays:
        warnings.append(f"{where}: 사진이 아닌 파일이 섞여 있습니다 → "
                        f"{' '.join(strays)} (원본은 폴더 밖에 두세요)")

    notice = folder / "notice"
    n_notice = len([p for p in notice.iterdir()
                    if p.is_file() and p.suffix.lower() == ".jpg" and p.stem.isdigit()]
                   ) if notice.is_dir() else 0

    return {
        "year": year, "half": half, "rel": rel, "icon": icon,
        "photos": n, "notice": n_notice,
        "thumb": special("thumb"),
        "poster": special("poster"),
        **{k: v for k, v in a.items() if k != "_block"},
    }


def js(s):
    """JS 작은따옴표 문자열로"""
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"


def render(acts):
    terms = {}
    for a in acts:
        terms.setdefault((a["year"], a["half"]), []).append(a)

    out = [START, "const TERMS = ["]
    for (year, half) in sorted(terms, reverse=True):
        group = sorted(terms[(year, half)], key=lambda x: x["date"], reverse=True)
        out.append("  {")
        out.append(f"    year: {year}, half: {half},")
        out.append("    activities: [")
        for i, a in enumerate(group):
            L = ["      {"]
            L.append(f"        date: {js(a['date'])},")
            if a.get("endDate"):
                L.append(f"        endDate: {js(a['endDate'])},")
            L.append(f"        title: {js(a['title'])},")
            if a.get("subtitle"):
                L.append(f"        subtitle: {js(a['subtitle'])},")
            L.append(f"        icon: {js(a['icon'])},")
            if a.get("place"):
                L.append(f"        place: {js(a['place'])},")
            if a.get("time"):
                L.append(f"        time: {js(a['time'])},")
            if a.get("people"):
                L.append(f"        people: {int(a['people'])},")
            if a.get("upcoming"):
                L.append("        upcoming: true,")
            if a.get("desc"):
                L.append(f"        desc: {js(a['desc'])},")
            if a.get("note"):
                L.append(f"        note: {js(a['note'])},")
            if a["thumb"]:
                L.append(f"        thumb: {js(a['thumb'])},")
            if a["poster"]:
                L.append(f"        poster: {js(a['poster'])},")
            if a["notice"]:
                L.append(f"        notice: seq({js(a['rel'] + '/notice')}, {a['notice']}),")
            L.append(f"        photos: seq({js(a['rel'])}, {a['photos']})")
            L.append("      }" + ("," if i < len(group) - 1 else ""))
            out.extend(L)
        out.append("    ]")
        out.append("  }" + ("," if (year, half) != min(terms) else ""))
    out.append("];")
    out.append(END)
    return "\n".join(out)


def main():
    check_only = "--check" in sys.argv

    if not DATA.exists():
        sys.exit(f"{DATA.name} 이 없습니다")
    if not HTML.exists():
        sys.exit(f"{HTML.name} 이 없습니다")

    raw = parse(DATA.read_text(encoding="utf-8"))
    acts = [a for a in (check(x) for x in raw) if a]

    if errors:
        print("고쳐야 할 것:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    for w in warnings:
        print("확인:", w)
    if warnings:
        print()

    # 표로 한 번 보여 준다
    by_term = {}
    for a in acts:
        by_term.setdefault((a["year"], a["half"]), []).append(a)
    for (year, half) in sorted(by_term, reverse=True):
        print(f"[{year} {'상반기' if half == 1 else '하반기'}]")
        for a in sorted(by_term[(year, half)], key=lambda x: x["date"], reverse=True):
            extra = " ".join(filter(None, [
                "썸네일" if a["thumb"] else "",
                "포스터" if a["poster"] else "",
                f"참고{a['notice']}" if a["notice"] else "",
                "예정" if a.get("upcoming") else "",
            ]))
            print(f"  {a['date']}  {a['title']:<14} 사진 {a['photos']:3d}장  {extra}")
        print()

    block = render(acts)
    html = HTML.read_text(encoding="utf-8")
    if START not in html or END not in html:
        sys.exit(f"{HTML.name} 에서 {START} ~ {END} 표시를 찾지 못했습니다")

    before = html[:html.index(START)]
    after = html[html.index(END) + len(END):]
    new = before + block + after

    if new == html:
        print("바뀐 내용 없음")
        return
    if check_only:
        print("(--check 라서 파일은 고치지 않았습니다. 바뀔 내용이 있습니다)")
        return

    HTML.write_text(new, encoding="utf-8")
    print(f"{HTML.name} 갱신 완료 - 활동 {len(acts)}개")


if __name__ == "__main__":
    main()
