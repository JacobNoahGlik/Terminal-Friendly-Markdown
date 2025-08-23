# Terminal Friendly Markdown (TFMD)

A fast, pretty **Markdown previewer for the terminal** (WSL/Linux/macOS).  
Renders headings, lists, tables, links, code blocks (with syntax highlighting), and more — with optional paging via `less` or a **mouse-wheel friendly TUI**.

---

## ✨ Features

- Clean, GitHub-style presets (`--theme github-dark|github-light`)
- Syntax-highlighted fenced code (`--code-theme …`; defaults follow theme)
- Optional Table of Contents (`--toc`)
- Soft wrapping to terminal width (`--soft-wrap`)
- YAML front-matter hiding (`--show-fm` to reveal)
- Two pager backends:
  - **less** (default): lightweight, `/` search, restores screen on quit
  - **tui** (Textual): mouse wheel + `j/k`, PgUp/PgDn, `g/G`, `q`
- Streams from **stdin** or reads files
- Works great in **WSL** and standard Linux terminals

---

## 🚀 Quick Start (recommended)

From the repo root:

```bash
# one-time setup (installs with pipx, injects Textual)
bash scripts/setup_tfmd.sh

# try it (GitHub dark look + mouse wheel)
tfmd README.md --toc --soft-wrap --backend tui --theme github-dark
```

> If `tfmd` isn’t found, open a new shell or:
> `export PATH="$HOME/.local/bin:$PATH"`

To uninstall later:

```bash
bash scripts/uninstall_tfmd.sh          # remove pipx app/venv
bash scripts/uninstall_tfmd.sh --purge  # also clean the pager lines from ~/.bashrc
```

---

## 🧰 Manual install options

### A) Global CLI via pipx

```bash
pipx install .
pipx inject tfmd textual           # for the TUI backend (mouse wheel)
tfmd --version
```

### B) Run from source (no pipx)

```bash
python -m venv .venv && source .venv/bin/activate
pip install rich textual
python tfmd/cli.py README.md --toc --soft-wrap
```

---

## 📖 Usage

Basic:

```bash
tfmd README.md
```

Popular options:

```bash
# GitHub-style themes
tfmd README.md --toc --soft-wrap --theme github-dark
tfmd README.md --toc --soft-wrap --theme github-light

# TUI pager (mouse wheel)
tfmd README.md --toc --soft-wrap --backend tui

# less pager always / never
tfmd README.md --pager always
tfmd README.md --pager never > out.txt

# keep page contents on exit (less -X)
tfmd README.md --leave-on-exit

# show front-matter and force width
tfmd README.md --show-fm --width 100

# pipe from stdin
cat README.md | tfmd --toc
```

### CLI flags (summary)

* `file` (optional): path to a Markdown file (or omit to read from `stdin`)
* `-p, --pager {auto,always,never}`: choose paging strategy (default: `auto`)
* `--backend {less,tui}`: pager backend (default: `less`)
* `--toc`: show a Table of Contents
* `--soft-wrap`: wrap long lines to the terminal width
* `--show-fm`: show YAML front matter (hidden by default)
* `--width N`: render to a specific width
* `--theme {default,light,dark,github-dark,github-light}`: UI theme
* `--code-theme NAME`: Pygments style for fenced code
  *(if omitted, follows the chosen `--theme`)*
* `--leave-on-exit`: keep content on screen when quitting `less`
* `--no-style`: disable custom styling
* `--version`: print version

---

## 🐞 Troubleshooting

* **“tfmd: command not found”**
  `pipx ensurepath && export PATH="$HOME/.local/bin:$PATH"`

* **TUI says “Textual not installed” (pipx users)**
  `pipx inject tfmd textual`

* **Unicode boxes instead of emoji/glyphs**
  Ensure UTF-8 and a font with good glyph coverage:

  ```bash
  export LANG=en_US.UTF-8
  export LC_ALL=en_US.UTF-8
  export LESSCHARSET=utf-8
  ```

  In Windows Terminal, set a Nerd Font or Cascadia Code PL.

* **less doesn’t clear on quit**
  Use default behavior (clears) or avoid `-X`. TFMD uses `less -RF` by default.
  To leave content on exit: `--leave-on-exit` (adds `-X`).

---

## 🧪 Test file

A ready-made demo lives at `tests/README_TEST.md`:

```bash
tfmd tests/README_TEST.md --toc --soft-wrap --theme github-dark --backend tui
```
