"""Settings loader. tools/config.json holds only non-secret settings; secrets are read from the
owner's private files at call time and never written anywhere inside the project."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(p):
    return open(os.path.expanduser(p)).read().strip()


def load():
    cfg = json.load(open(os.path.join(ROOT, "tools", "config.json")))
    g = json.loads(_read("~/.config/gravitex/credentials-ent.json"))
    cfg["gravitex"]["key"] = g["key"]
    cfg["gravitex"]["url"] = (g.get("url") or cfg["gravitex"]["url"]).rstrip("/")
    cfg["autodl"]["token"] = _read("~/.config/autodl-art/token")
    cfg.setdefault("minimax", {})["key"] = _read("~/.config/kllm/minimax-ir-key")
    return cfg
