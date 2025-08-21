# Terminal Friendly Markdown

## install deps
```bash
python -m venv .venv && source .venv/bin/activate
pip install rich
```

## run on a file
```bash
python tfmd/cli.py README.md
```

## pipe from stdin
```bash
cat README.md | python tfmd/cli.py --toc
```

## always page through less -R
```bash
python tfmd/cli.py README.md --pager always
```

## render without paging (useful when redirecting to a file)
```bash
python tfmd/cli.py README.md --pager never > out.txt
```

## soft wrap long lines, show (otherwise hidden) YAML front-matter
```bash
python tfmd/cli.py README.md --soft-wrap --show-fm
```

## force a width (useful for screenshots)
```bash
python tfmd/cli.py README.md --width 100
```
