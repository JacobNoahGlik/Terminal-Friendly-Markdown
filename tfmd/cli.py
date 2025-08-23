#!/usr/bin/env python3
# TFMD — Terminal Friendly Markdown (v1)
# Python 3.9+ (uses typing.Optional/Tuple for 3.9 compatibility)
import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from tfmd import __version__

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

# --- Helpers -----------------------------------------------------------------

YAML_FM_RE = re.compile(r"(?s)^\s*---\n.*?\n---\s*\n")

DEFAULT_THEME = Theme({
    "markdown.h1": "bold underline",
    "markdown.h2": "bold",
    "markdown.h3": "bold",
    "markdown.code": "none",
    "markdown.link": "underline",
    "markdown.hr": "dim",
    "tfmd.toc.header": "bold",
    "tfmd.toc.item": "dim",
})

GH_DARK = Theme({
    "markdown.h1": "bold white",
    "markdown.h2": "bold white",
    "markdown.h3": "bold white",
    "markdown.link": "underline cyan",
    "markdown.hr": "color(240)",
    "tfmd.toc.header": "bold",
    "tfmd.toc.item": "dim",
})

GH_LIGHT = Theme({
    "markdown.h1": "bold black",
    "markdown.h2": "bold black",
    "markdown.h3": "bold black",
    "markdown.link": "underline blue",
    "markdown.hr": "color(246)",
    "tfmd.toc.header": "bold",
    "tfmd.toc.item": "dim",
})

def strip_front_matter(text: str) -> Tuple[str, Optional[str]]:
    """Return (content, front_matter_text_or_none)."""
    m = YAML_FM_RE.match(text)
    if not m:
        return text, None
    fm = m.group(0)
    return text[m.end():], fm

def extract_headings(md_text: str) -> List[Tuple[int, str]]:
    """Very simple heading extractor (#..######). Returns list of (level, text)."""
    out: List[Tuple[int, str]] = []
    for line in md_text.splitlines():
        if not line.startswith("#"):
            continue
        m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if m:
            out.append((len(m.group(1)), m.group(2)))
    return out

def make_toc_table(headings: List[Tuple[int, str]]) -> Table:
    tbl = Table.grid(expand=True)
    tbl.add_column(justify="left", ratio=1, no_wrap=True)
    if not headings:
        tbl.add_row("[dim]No headings found[/]")
        return tbl
    for lvl, text in headings:
        indent = "  " * (lvl - 1)
        bullet = "•"
        tbl.add_row(f"{indent}{bullet} [tfmd.toc.item]{text}[/]")
    return tbl

# --- CLI ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tfmd",
        description="Terminal Friendly Markdown — a Markdown previewer for WSL/Linux."
    )
    p.add_argument("file", nargs="?", help="Markdown file (or omit to read stdin)")
    p.add_argument("-p", "--pager", choices=["auto", "always", "never"], default="auto",
                   help="Page with less -R (default: auto if stdout is a TTY and less is available).")
    p.add_argument("--soft-wrap", action="store_true",
                   help="Wrap long lines to terminal width.")
    p.add_argument("--toc", action="store_true",
                   help="Show a Table of Contents before the document.")
    p.add_argument("--show-fm", action="store_true",
                   help="Show YAML front matter (hidden by default).")
    p.add_argument("--width", type=int, default=None,
                   help="Render width (defaults to terminal width).")
    p.add_argument("--theme",
        choices=["default", "light", "dark", "github-dark", "github-light"],
        default="default",
        help="Quick style presets.")
    p.add_argument("--no-style", action="store_true",
                   help="Disable custom theme styling (plain Rich defaults).")
    p.add_argument("--code-theme", default=None,
        help="Pygments theme for fenced code blocks (e.g. github-dark, github-light, monokai, dracula).")
    p.add_argument("--version", action="version", version=f"tfmd {__version__}")
    return p

def choose_theme(name: str) -> Optional[Theme]:
    if name == "default":
        return DEFAULT_THEME
    if name == "light":
        return GH_LIGHT
    if name == "dark":
        return GH_DARK
    if name == "github-dark":
        return GH_DARK
    if name == "github-light":
        return GH_LIGHT
    return None

def should_page(pager_flag: str, console: Console) -> bool:
    if pager_flag == "always":
        return True
    if pager_flag == "never":
        return False
    # auto
    try:
        import shutil
        has_less = shutil.which("less") is not None
    except Exception:
        has_less = False
    return console.is_terminal and has_less

# --- Main --------------------------------------------------------------------

def load_text(path_arg: Optional[str]) -> Tuple[str, Optional[Path]]:
    if path_arg:
        p = Path(path_arg)
        try:
            return p.read_text(encoding="utf-8"), p
        except UnicodeDecodeError:
            return p.read_bytes().decode("utf-8", errors="replace"), p
    else:
        data = sys.stdin.read()
        return data, None

def render_doc(console: Console, text: str, width: Optional[int],
               show_toc: bool, show_fm: bool, soft_wrap: bool,
               code_theme: str = "github-dark"):
    content, fm = strip_front_matter(text)
    headings = extract_headings(content)

    if show_toc:
        toc_panel = Panel(
            make_toc_table(headings),
            title="[tfmd.toc.header]Table of Contents[/]",
            expand=False,
            border_style="dim",
        )
        console.print(toc_panel, width=width)
        console.print()

    if show_fm and fm:
        console.print(Panel.fit(Syntax(fm.strip(), "yaml", word_wrap=soft_wrap),
                                title="front-matter", border_style="dim"))
        console.print()

    md = Markdown(
        content,
        code_theme=code_theme,   # <-- uses Pygments theme for fenced code
        justify="left",          # closer to GitHub layout
        inline_code_lexer="",
        hyperlinks=True,
    )
    console.print(md, width=width, soft_wrap=soft_wrap)

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    theme = None if args.no_style else choose_theme(args.theme)
    console = Console(theme=theme, force_terminal=None, width=args.width, record=False)

    code_theme = args.code_theme
    if code_theme is None:
        code_theme = "github-light" if args.theme in ("github-light", "light") else "github-dark"

    text, _path = load_text(args.file)

    use_pager = should_page(args.pager, console)

    if use_pager:
        with console.pager(styles=True):
            render_doc(console, text, args.width, args.toc, args.show_fm, args.soft_wrap,
                       code_theme=code_theme)
    else:
        render_doc(console, text, args.width, args.toc, args.show_fm, args.soft_wrap,
                   code_theme=code_theme)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
