#!/usr/bin/env python3
# TFMD — Terminal Friendly Markdown (v1)
# Python 3.9+ (uses typing.Optional/Tuple for 3.9 compatibility)
import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme
from rich.text import Text

# --- Helpers -----------------------------------------------------------------

YAML_FM_RE = re.compile(r"(?s)^\s*---\n.*?\n---\s*\n")

DEFAULT_THEME = Theme({
    "markdown.h1": "bold bright_cyan",      # was bold underline
    "markdown.h2": "bold bright_white",
    "markdown.h3": "bold",
    "markdown.link": "underline cyan",
    "markdown.code": "bright_white on grey11",   # inline code only (not fenced)
    "markdown.hr": "grey35",                      # rules less bright
    "tfmd.toc.header": "bold",
    "tfmd.toc.item": "dim",
})

def controls_banner() -> Panel:
    t = Text()
    t.append("Controls: ", style="bold")
    t.append("q", style="bold"); t.append(" quit   ")
    t.append("/", style="bold"); t.append(" search   ")
    t.append("n/N", style="bold"); t.append(" next/prev   ")
    t.append("g/G", style="bold"); t.append(" top/bottom   ")
    t.append("h", style="bold"); t.append(" help   ")
    t.append("↑/↓/PgUp/PgDn", style="bold"); t.append(" scroll")
    return Panel(t, border_style="dim")

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

# --- TUI Pager (optional) -----------------------------------------------------
def run_tui_pager(content: str, code_theme: str) -> int:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import ScrollableContainer
        from textual.widgets import Static
        from rich.markdown import Markdown
    except Exception as e:
        Console().print("[red]Textual is not installed for tfmd's environment.[/]\n"
                        "If using pipx: pipx inject tfmd textual")
        return 1

    md = Markdown(content, code_theme=code_theme, hyperlinks=True)

    class TFMDTUI(App):
        CSS = """
        #controls { color: #a0a0a0; padding: 0 1; }  /* hex color instead of 'grey70' */
        #scroll { height: 1fr; }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("j", "down", "Down"),
            ("k", "up", "Up"),
            ("g", "home", "Top"),
            ("G", "end", "Bottom"),
            ("pageup", "page_up", "PgUp"),
            ("pagedown", "page_down", "PgDn"),
            ("up", "up", "Up"),
            ("down", "down", "Down"),
        ]

        def compose(self) -> ComposeResult:
            yield Static(
                "Controls: q quit  j/k up/down  PgUp/PgDn  g/G top/bottom  (mouse wheel works)",
                id="controls"
            )
            with ScrollableContainer(id="scroll"):
                yield Static(md, expand=True)

        def _scroll(self) -> ScrollableContainer:
            return self.query_one("#scroll", ScrollableContainer)

        async def action_up(self):        await self._scroll().scroll_up(3)
        async def action_down(self):      await self._scroll().scroll_down(3)
        async def action_page_up(self):   await self._scroll().scroll_page_up()
        async def action_page_down(self): await self._scroll().scroll_page_down()
        async def action_home(self):      await self._scroll().scroll_to(y=0)
        async def action_end(self):
            sc = self._scroll()
            await sc.scroll_to(y=sc.virtual_size.height)

    TFMDTUI().run()
    return 0


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
    p.add_argument("--theme", choices=["default", "light", "dark"], default="default",
            help="Quick style presets.")
    p.add_argument("--no-style", action="store_true",
            help="Disable custom theme styling (plain Rich defaults).")
    p.add_argument("--leave-on-exit", action="store_true",
            help="Leave content on screen when exiting the pager (less -X).")
    p.add_argument("--code-theme", default="monokai",
            help="Pygments theme for fenced code blocks (e.g. monokai, dracula, github-dark, github-light, solarized-dark, solarized-light).")
    p.add_argument("--backend", choices=["less", "tui"], default="less",
            help="Pager backend to use when paging (default: less).")
    return p

def choose_theme(name: str) -> Optional[Theme]:
    if name == "default":
        return DEFAULT_THEME
    if name == "light":
        return Theme({
            **DEFAULT_THEME.styles,
            "markdown.h1": "bold blue",
            "markdown.h2": "bold black",
            "markdown.link": "underline blue",
            "markdown.code": "black on #f2f2f2",
            "markdown.hr": "grey66",
        })
    if name == "dark":
        # keep dark but bump contrast a bit more
        return Theme({
            **DEFAULT_THEME.styles,
            "markdown.h1": "bold bright_cyan",
            "markdown.h2": "bold white",
            "markdown.hr": "grey42",
        })
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

def render_doc(
    console,
    text: str,
    width: Optional[int],
    show_toc: bool,
    show_fm: bool,
    soft_wrap: bool,
    show_controls: bool = False,
    code_theme: str = "monokai",          # <-- add this
):
    content, fm = strip_front_matter(text)
    headings = extract_headings(content)

    if show_controls:
        console.print(controls_banner(), width=width)
        console.print()

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
        code_theme=code_theme,             # <-- use it here
        justify=None,
        inline_code_lexer="",
        hyperlinks=True,
    )
    console.print(md, width=width, soft_wrap=soft_wrap)

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    theme = None if args.no_style else choose_theme(args.theme)
    console = Console(theme=theme, force_terminal=None, width=args.width, record=False)

    text, _path = load_text(args.file)

    use_pager = should_page(args.pager, console)
    
    if use_pager and args.backend == "tui":
        # show TOC/front-matter inside TUI too (optional): simplest is just feed content
        content, fm = strip_front_matter(text)
        return run_tui_pager(content, code_theme=args.code_theme)

    if use_pager and args.backend == "less":
        # make 'less' behave well with rich output
        leave_on_exit = getattr(args, "leave_on_exit", False)
        pager_opts = "-RF" if not leave_on_exit else "-RFX"   # -R colors, -F quit if one screen, -X leave screen
        os.environ.setdefault("LESS", pager_opts)
        os.environ.setdefault("LESSCHARSET", "utf-8")
        os.environ.setdefault("PAGER", f"less {pager_opts}")
        with console.pager(styles=True):
            render_doc(console, text, args.width, args.toc, args.show_fm, args.soft_wrap,
                   show_controls=True, code_theme=args.code_theme)
    else:
        render_doc(console, text, args.width, args.toc, args.show_fm, args.soft_wrap,
               show_controls=False, code_theme=args.code_theme)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
