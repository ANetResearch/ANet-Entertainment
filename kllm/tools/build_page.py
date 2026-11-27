#!/usr/bin/env python3
"""build_page.py: builds the keyed comparison page of the kLLM samples.

    python3 kllm/tools/build_page.py --manifest kllm/samples/manifest.json \
        --comparisons kllm/samples/comparisons.json --key-file KEY_FILE --out OUT/index.html

The manifest and the comparison records are joined into one JSON payload, which is encrypted with a key derived from
the access key (PBKDF2-SHA256, 600,000 iterations, random 16-byte salt) using AES-256-GCM (random 12-byte nonce).
The page (page.html beside this script) carries only the ciphertext; the browser decrypts it with WebCrypto after the
access key is entered. Without the key the page shows the key prompt and nothing else.

Requires Python 3.8+ and the "cryptography" package. The access key is read from KEY_FILE and is never written out.
"""
import argparse
import base64
import hashlib
import json
import os
import sys

ITERATIONS = 600_000


def payload_bytes(manifest, comparisons):
    data = {
        "generated": manifest.get("generated"),
        "sets": manifest.get("sets", {}),
        "set_order": manifest.get("set_order", []),
        "series": manifest.get("series", {}),
        "series_order": manifest.get("series_order", []),
        "series_note": manifest.get("series_note", ""),
        "schemes": manifest.get("schemes", {}),
        "components_note": manifest.get("components_note", ""),
        "releases": manifest.get("releases", {}),
        "entries": manifest.get("entries", []),
        "themes": comparisons.get("themes", []),
        "comparisons": comparisons.get("comparisons", []),
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def encrypt(plain, passphrase):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        sys.exit("build_page.py needs the 'cryptography' package")
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS, 32)
    ct = AESGCM(key).encrypt(iv, plain, None)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITERATIONS, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--comparisons", required=True)
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "page.html"))
    ap.add_argument("--print-payload-sha256", action="store_true",
                    help="print the SHA-256 of the plaintext payload and the template, then exit without writing")
    a = ap.parse_args()
    manifest = json.load(open(a.manifest, encoding="utf-8"))
    comparisons = json.load(open(a.comparisons, encoding="utf-8"))
    plain = payload_bytes(manifest, comparisons)
    template = open(a.template, encoding="utf-8").read()
    if a.print_payload_sha256:
        print(hashlib.sha256(plain).hexdigest(), hashlib.sha256(template.encode("utf-8")).hexdigest())
        return
    passphrase = open(os.path.expanduser(a.key_file), encoding="utf-8").read().strip()
    if len(passphrase) < 16:
        sys.exit("the access key must have at least 16 characters")
    box = json.dumps(encrypt(plain, passphrase), separators=(",", ":"))
    marker = "<!--PAYLOAD-->"
    if template.count(marker) != 1:
        sys.exit("template must contain the payload marker exactly once")
    page = template.replace(marker, '<script id="payload" type="application/json">' + box + "</script>")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    open(tmp, "w", encoding="utf-8").write(page)
    os.replace(tmp, a.out)
    print(f"wrote {a.out}: {len(plain)} bytes of payload, {len(page)} bytes of page")


if __name__ == "__main__":
    main()
