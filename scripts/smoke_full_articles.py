#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manual smoke test: multi-lingual article translation against a real GGUF model.

Not a unit test — this loads model weights and takes minutes. Run it by hand:

    .venv/bin/python scripts/smoke_full_articles.py
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from translator_cli import TranslatorCLI

FULL_INPUT = """English Test Article — Why Convenience Can Become a Problem

Modern technology has made many everyday tasks faster and easier. People can order food, pay bills, contact friends, and find information without leaving their homes. These services save time and often reduce unnecessary effort, which is why convenience is usually seen as something positive.

Japanese Test Article — 効率だけを求めればよいわけではない

現代では、仕事や勉強をできるだけ効率よく進めることが重要だと考えられている。短い時間で多くのことを終えられれば、その分だけ自由な時間が増え、より充実した生活を送れるように思える。

Russian Test Article — Почему не всегда полезно спешить

В современном мире скорость часто считается признаком эффективности. Люди стараются быстрее работать, быстрее принимать решения и даже быстрее отдыхать, потому что им кажется, что каждая сэкономленная минута обязательно должна быть использована с пользой."""


def main():
    cli = TranslatorCLI()
    cli.init_engine()
    cli.target_lang_key = "1"

    print("Testing full multi-lingual article translation...")
    cli.stream_translate(FULL_INPUT)
    print("Finished!")


if __name__ == "__main__":
    main()
