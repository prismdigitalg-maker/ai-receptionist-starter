#!/usr/bin/env python3
"""AI Receptionist — a working receptionist on OpenRouter.

One key does everything:  ears (speech-to-text) · brain (language model) · voice (text-to-speech).
Pure Python standard library — no dependencies to install.

    export OPENROUTER_API_KEY=sk-or-...
    python server.py
    open http://localhost:8765

Edit config.yaml to change the business, the assistant's name, hours, models and voice.
"""
import os, json, uuid, base64, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OR = "https://openrouter.ai/api/v1"
KEY = lambda: os.environ["OPENROUTER_API_KEY"]


def load_cfg():
    cfg = {}
    for line in (ROOT / "config.yaml").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line and ":" in line:
            k, v = line.split(":", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


CFG = load_cfg()


def system_prompt():
    return (
        f"You are {CFG.get('assistant_name','Alex')}, the warm, efficient phone receptionist for "
        f"{CFG.get('brand_name','the business')} in {CFG.get('brand_city','')}. "
        f"Answer in ONE short spoken sentence (max 25 words). "
        f"Services: {CFG.get('services','')}. Opening hours: {CFG.get('opening_hours','')}. "
        f"Offer the next available appointment and ask for the caller's name and number. "
        f"Never say you are an AI unless asked. No emojis."
    )


def _post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {KEY()}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def _sniff(b):
    if b[:4] == b"RIFF":
        return "audio.wav", "audio/wav"
    if b[:4] == b"OggS":
        return "audio.ogg", "audio/ogg"
    if b[4:8] == b"ftyp":
        return "audio.m4a", "audio/mp4"
    return "audio.webm", "audio/webm"


def transcribe(raw):
    filename, ctype = _sniff(raw)
    b = "----b" + uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{CFG.get("stt_model")}\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n").encode() + raw + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(OR + "/audio/transcriptions", data=body,
        headers={"Authorization": f"Bearer {KEY()}", "Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=60)).get("text", "").strip()


def reply(text):
    r = _post_json(OR + "/chat/completions", {"model": CFG.get("llm_model"), "max_tokens": 80,
        "messages": [{"role": "system", "content": system_prompt()}, {"role": "user", "content": text}]})
    return r["choices"][0]["message"]["content"].strip().strip('"')


def speak(text):
    req = urllib.request.Request(OR + "/audio/speech",
        data=json.dumps({"model": CFG.get("tts_model"), "input": text,
                         "voice": CFG.get("tts_voice"), "response_format": "mp3"}).encode(),
        headers={"Authorization": f"Bearer {KEY()}", "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=60).read()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, ctype, body):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            self._send(200, "text/html", (ROOT / "static/index.html").read_bytes())
        elif p == "/caller.mp3" and (ROOT / "static/caller.mp3").exists():
            self._send(200, "audio/mpeg", (ROOT / "static/caller.mp3").read_bytes())
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            if self.path == "/turn":
                text = transcribe(raw)
                if not text:
                    return self._send(200, "application/json", b'{"transcript":"","reply":"","audio":""}')
                ans = reply(text); mp3 = speak(ans)
                return self._send(200, "application/json", json.dumps(
                    {"transcript": text, "reply": ans, "audio": base64.b64encode(mp3).decode()}).encode())
        except Exception as e:
            return self._send(500, "application/json", json.dumps({"error": str(e)}).encode())
        self._send(404, "text/plain", b"not found")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"AI Receptionist → http://localhost:{port}   (Ctrl-C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
