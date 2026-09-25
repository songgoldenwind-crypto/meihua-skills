"""Check that the public Skill is self-contained and method-only."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN = ("/Users/", "PRIVATE COMMERCIAL LICENSE")
SOURCE_MARKERS = re.compile(r"《[^》]+》|\bB[0-9]{2}\b|(?:PDF|OCR)[^\n]{0,12}(?:页|报告)|物理页|出版社|source_url")
REQUIRED = (
    "SKILL.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "scripts/meihua-engine/paipan.py",
    "scripts/meihua-engine/vendor/MeihuaYiAI/LICENSE",
    "scripts/meihua-engine/vendor/lunar-python/LICENSE",
)


def main() -> int:
    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f"缺少必要文件: {name}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in (".md", ".py", ".json", ".sh", ".yml"):
            continue
        if ".git" in path.parts or "vendor" in path.parts or path == Path(__file__).resolve():
            continue
        content = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN:
            if needle in content:
                errors.append(f"{path.relative_to(ROOT)} 包含禁止公开的来源标识: {needle}")
        marker = SOURCE_MARKERS.search(content)
        if marker:
            errors.append(f"{path.relative_to(ROOT)} 包含书目、页码或来源标识: {marker.group(0)}")
        if path.suffix != ".md":
            continue
        for target in LINK.findall(content):
            target = unquote(target.split("#", 1)[0]).strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).exists():
                errors.append(f"{path.relative_to(ROOT)} 链接无效: {target}")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".pdf":
            errors.append(f"不得分发原书 PDF: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("公开仓库结构、链接、许可证与私有路径检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
