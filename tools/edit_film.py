#!/usr/bin/env python3
"""Cut one series episode with the second-pass editor.  usage: edit_film.py EP OUT.mp4 [--end card.png]"""
import os, sys
os.environ["EP"] = f"ep{int(sys.argv[1]):02d}"
sys.argv = [sys.argv[0]] + sys.argv[2:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_film2
edit_film2.main()
