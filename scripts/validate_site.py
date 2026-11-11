#!/usr/bin/env python3
"""Valida a estrutura e as referencias locais de um website estatico."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "carta.html", "esqueceu_senha.html")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = False
        self.has_html = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.has_html = True
        if tag == "title":
            self.title = True
        if tag in ("script", "img", "source", "video", "audio"):
            key = "src"
        elif tag in ("link", "a"):
            key = "href"
        else:
            return
        if attrs.get(key):
            self.links.append((tag, attrs[key]))


def local_file(url):
    value = url.strip()
    if not value or value.startswith(("#", "//")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path or path.startswith("/"):
        return None  # raiz absoluta nao e validada por este verificador
    return path


def main():
    errors = []
    checked = 0
    for page in PAGES:
        target = ROOT / page
        if not target.is_file():
            errors.append(f"Pagina ausente: {page}")
            continue
        parser = PageParser()
        parser.feed(target.read_text(encoding="utf-8"))
        if not parser.has_html or not parser.title:
            errors.append(f"HTML basico incompleto: {page}")
        for tag, url in parser.links:
            path = local_file(url)
            if path is None:
                continue
            resolved = (target.parent / path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
                errors.append(f"{page}: {tag} aponta para arquivo ausente: {url}")
            checked += 1

    for css in ROOT.rglob("*.css"):
        if ".git" in css.parts:
            continue
        content = css.read_text(encoding="utf-8")
        for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", content):
            path = local_file(url)
            if path is None:
                continue
            resolved = (css.parent / path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
                errors.append(f"{css.relative_to(ROOT)}: recurso CSS ausente: {url}")
            checked += 1

    if errors:
        print("FALHA na validacao:\n" + "\n".join(f"- {e}" for e in errors))
        return 1
    print(f"OK: {len(PAGES)} paginas e {checked} referencias locais verificadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
