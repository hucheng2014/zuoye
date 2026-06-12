from __future__ import annotations

import argparse
import html
import json
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_SOURCE = Path(r"C:\Users\BERN7P\AppData\Local\Temp\feishu_downloads\henan_preview_type8.bin")
DEFAULT_OUTPUT = Path(r"C:\Users\BERN7P\AppData\Local\CodexAppenAssets\henan_orthography_rows.json")


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_td = False
        self.in_th = False
        self.in_tr = False
        self.rows: list[list[str]] = []
        self.current_row: list[str] = []
        self.current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif tag in ("td", "th"):
            self.in_td = tag == "td"
            self.in_th = tag == "th"
            self.current_cell = []
        elif tag == "br" and (self.in_td or self.in_th):
            self.current_cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and (self.in_td or self.in_th):
            cell = html.unescape("".join(self.current_cell)).replace("\xa0", " ").strip()
            self.current_row.append(cell)
            self.current_cell = []
            self.in_td = False
            self.in_th = False
        elif tag == "tr" and self.in_tr:
            if any(cell for cell in self.current_row):
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_tr = False

    def handle_data(self, data: str) -> None:
        if self.in_td or self.in_th:
            self.current_cell.append(data)


def extract_rows(source: Path) -> list[list[str]]:
    parser = TableParser()
    parser.feed(source.read_text(encoding="utf-8", errors="ignore"))
    return parser.rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = extract_rows(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "source": str(args.source),
                "output": str(args.output),
                "rowCount": len(rows),
                "preview": rows[:12],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
