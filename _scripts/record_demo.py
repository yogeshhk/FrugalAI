"""Record a running demo page: step screenshots (PNG) and a screen video (MP4), with headless Edge over its debugging
port. No browser automation package is needed, only websocket-client and ffmpeg on PATH.

    python _scripts/record_demo.py <scenario> --url http://localhost:8601/ --out <folder> [--no-video] [--gif]

Start the page first (streamlit run app.py in the project folder) with its models loaded. A scenario is a list of
steps in SCENARIOS below. Waits for a model are sped up in the video (the factor is printed on the last frame's
caption in the deck, and the page itself shows the real seconds of every run).
"""

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import websocket  # websocket-client

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9334
WIDTH, HEIGHT = 1500, 940
SPEEDUP = 4.0          # waits for a model run at this speed in the video

# Steps: ("goto",), ("click", button text), ("wait", text that must appear), ("type", text, nth textarea or input),
# ("shot", name) what is on screen, ("full", name) the whole page, ("pause", seconds), ("top",),
# ("scroll", text to bring into view)
SCENARIOS = {
    "voice-form": [
        ("goto",), ("wait", "Speak a form"), ("pause", 2), ("shot", "frugal_voice_start"),
        ("click", "Sample recordings"), ("pause", 1.5),
        ("click", "Use mr-asha-01"), ("wait", "Request for the next system"), ("pause", 1),
        ("scroll", "Heard"), ("pause", 2), ("shot", "frugal_voice_filled"),
        ("scroll", "Still to ask"), ("pause", 2),
        ("click", "Type"), ("pause", 1), ("type", "मोबाईल नंबर नऊ आठ दोन तीन चार पाच सहा सात आठ नऊ"),
        ("click", "Fill from text"), ("wait", "Heard (typed)"), ("pause", 1),
        ("scroll", "Heard"), ("pause", 2), ("shot", "frugal_voice_followup"),
        ("click", "Confirm and save"), ("wait", "Saved on this laptop only"),
        ("scroll", "Request for the next system", 260), ("pause", 2.5), ("shot", "frugal_voice_saved"),
    ],
    "quantum-wiki": [
        ("goto",), ("wait", "Base model and RAG"), ("pause", 2),
        ("click", "What is the pass mark for QT 03?"), ("wait", "Base model + RAG"),
        ("scroll", "Base model and RAG", 200), ("pause", 2.5), ("shot", "frugal_rag_passmark"),
        ("click", "What is the title of QT 08?"), ("wait", "Base model + RAG"),
        ("scroll", "Base model and RAG", 200), ("pause", 2.5), ("shot", "frugal_rag_title"),
    ],
    "wiki-rag": [
        ("goto",), ("wait", "Ask your own notes"), ("pause", 2),
        ("click", "How often is the kitchen water filter cartridge replaced?"), ("wait", "Notes it read"),
        ("scroll", "How often is the kitchen water filter cartridge replaced?", 60), ("pause", 2.5),
        ("shot", "frugal_wiki_answer"),
        ("click", "Who won the cricket match yesterday?"), ("wait", "Notes it read"),
        ("scroll", "Who won the cricket match yesterday?", 60), ("pause", 2.5), ("shot", "frugal_wiki_refuse"),
        ("click", "What is 2400 * 0.15"), ("wait", "calculator, no model"),
        ("scroll", "What is 2400 * 0.15", 60), ("pause", 2),
        ("click", "Add a note (the index updates in seconds, nothing is retrained)"), ("pause", 1.5),
        ("scroll", "File name", 120), ("pause", 1.5),
        ("click", "Save note and update the index"), ("wait", "When is my next blood test?"), ("wait", "Notes it read"),
        ("pause", 1), ("scroll", "When is my next blood test?", 60), ("pause", 2.5), ("shot", "frugal_wiki_newnote"),
    ],
    "workflow-agent": [
        ("goto",), ("wait", "A small model inside a workflow"), ("pause", 2),
        ("click", "What is the price of wheat in Pune market today?"), ("wait", "Facts from the tool"),
        ("scroll", "A small model inside a workflow", 200), ("pause", 2.5), ("shot", "frugal_flow_price"),
        ("click", "Is wheat selling for 9999 rupees in Pune?"), ("wait", "Facts from the tool"),
        ("scroll", "A small model inside a workflow", 200), ("pause", 2.5), ("shot", "frugal_flow_trap"),
    ],
    "workflow-agent-faq": [
        ("goto",), ("wait", "A small model inside a workflow"), ("pause", 1), ("click", "Already covered?"),
        ("pause", 2), ("click", "Does a quantum computer try every answer at once?"), ("wait", "Where it already appears"),
        ("scroll", "Closest FAQ entry", 160), ("pause", 2.5), ("shot", "frugal_flow_faq_covered"),
        ("click", "What is a surface code?"), ("wait", "Where it already appears"),
        ("scroll", "Closest FAQ entry", 160), ("pause", 2.5), ("shot", "frugal_flow_faq_new"),
    ],
    "finetune-slm": [
        ("goto",), ("wait", "A tiny model, trained on this laptop"), ("pause", 2),
        ("click", "Heavy wind expeted at Amravati in two days, is that right?"), ("wait", "prompt tokens"),
        ("scroll", "A tiny model, trained on this laptop", 200), ("pause", 2.5), ("shot", "frugal_tune_weather"),
        ("click", "Is it worth fixing an old seed drill or should I buy new?"), ("wait", "prompt tokens"),
        ("scroll", "A tiny model, trained on this laptop", 200), ("pause", 2.5), ("shot", "frugal_tune_repair"),
    ],
}


class Page:
    def __init__(self, port: int):
        deadline = time.time() + 30
        while True:
            try:
                targets = json.load(urllib.request.urlopen("http://localhost:%d/json" % port, timeout=2))
                page = next(t for t in targets if t["type"] == "page")
                break
            except Exception:
                if time.time() > deadline:
                    raise RuntimeError("Edge did not open its debugging port")
                time.sleep(0.5)
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=120, suppress_origin=True)
        self.n = 0
        self.frames = []           # (timestamp, path)
        self.frame_dir = None
        self.results = {}
        self.lock = threading.Lock()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        while True:
            try:
                msg = json.loads(self.ws.recv())
                if msg.get("method") == "Page.screencastFrame":
                    p = msg["params"]
                    if self.frame_dir is not None:
                        path = self.frame_dir / ("f%06d.jpg" % len(self.frames))
                        path.write_bytes(base64.b64decode(p["data"]))
                        self.frames.append((p["metadata"]["timestamp"], path))
                    self._send("Page.screencastFrameAck", sessionId=p["sessionId"])
                elif "id" in msg:
                    with self.lock:
                        self.results[msg["id"]] = msg
            except Exception:            # the browser closed the connection: recording is over
                return

    def _send(self, method, **params):
        with self.lock:
            self.n += 1
            n = self.n
        self.ws.send(json.dumps({"id": n, "method": method, "params": params}))
        return n

    def call(self, method, **params):
        n = self._send(method, **params)
        deadline = time.time() + 120
        while time.time() < deadline:
            with self.lock:
                if n in self.results:
                    return self.results.pop(n).get("result", {})
            time.sleep(0.02)
        raise RuntimeError("no answer to " + method)

    def js(self, expression):
        return self.call("Runtime.evaluate", expression=expression, returnByValue=True,
                         awaitPromise=True).get("result", {}).get("value")


def busy(page: Page) -> bool:
    return bool(page.js("!!document.querySelector('[data-testid=\"stStatusWidget\"] button, "
                        "[data-testid=\"stSpinner\"]')"))


def wait_text(page: Page, text: str, timeout: float = 600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        body = page.js("document.body.innerText") or ""
        if text in body and not busy(page):
            return
        time.sleep(0.7)
    raise RuntimeError("timed out waiting for %r" % text)


def click(page: Page, text: str, timeout: float = 20):
    """Click the last button (or tab, or summary) showing `text`; a page may draw its buttons a few seconds after its
    title, so look again for up to `timeout` seconds before giving up."""
    script = """(() => { const t = %s;
        const els = [...document.querySelectorAll('button, [role="tab"], summary')].filter(b =>
            b.innerText.trim() === t || (b.tagName === 'SUMMARY' && b.innerText.trim().endsWith(t)));
        if (!els.length) return false; const b = els[els.length - 1];
        b.scrollIntoView({block: 'center'}); b.click(); return true; })()""" % json.dumps(text)
    t0 = time.time()
    while not page.js(script):
        if time.time() - t0 > timeout:
            raise RuntimeError("no button %r" % text)
        time.sleep(0.7)


def scroll_to(page: Page, text: str, above: int = 140):
    """Bring the last element showing `text` (buttons excluded) to the top, leaving `above` pixels of context."""
    page.js("""(() => { const t = %s; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let hit = null;
        while (w.nextNode()) { const n = w.currentNode;
            if (n.nodeValue.includes(t) && !n.parentElement.closest('button')) hit = n.parentElement; }
        if (!hit) return false;
        let s = hit.parentElement;
        while (s && !(s.scrollHeight > s.clientHeight + 5 && getComputedStyle(s).overflowY !== 'visible')) s = s.parentElement;
        s = s || document.scrollingElement;
        const top = hit.getBoundingClientRect().top - s.getBoundingClientRect().top + s.scrollTop - %d;
        s.scrollTo({top: Math.max(top, 0), behavior: 'smooth'}); return true; })()""" % (json.dumps(text), above))


def type_into(page: Page, text: str, selector: str = "textarea"):
    ok = page.js("""(() => { const els = [...document.querySelectorAll(%s)].filter(e => e.offsetParent !== null);
        const e = els[0]; if (!e) return false; e.scrollIntoView({block: 'center'}); e.focus(); return true; })()"""
                 % json.dumps(selector))
    if not ok:
        raise RuntimeError("nothing visible matches %r" % selector)
    for i in range(0, len(text), 3):                      # a few characters at a time, so the video shows typing
        page.call("Input.insertText", text=text[i:i + 3])
        time.sleep(0.08)
    page.js("document.activeElement.blur()")
    time.sleep(0.8)


def view_shot(page: Page, path: Path):
    """What is on screen now (1500 x 940, sidebar included): the shape that fits a slide."""
    path.write_bytes(base64.b64decode(page.call("Page.captureScreenshot", format="png")["data"]))


def screenshot(page: Page, path: Path):
    """The page's main block as one PNG, at full height (the viewport is stretched for the shot, then restored)."""
    h = page.js("Math.ceil(document.querySelector('.block-container').getBoundingClientRect().height) + 140") or HEIGHT
    y = page.js("document.querySelector('[data-testid=\"stMain\"]') ? "
                "document.querySelector('[data-testid=\"stMain\"]').scrollTop : 0") or 0
    page.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=max(int(h), HEIGHT), deviceScaleFactor=1,
              mobile=False)
    time.sleep(1.2)
    data = page.call("Page.captureScreenshot", format="png")["data"]
    path.write_bytes(base64.b64decode(data))
    page.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=HEIGHT, deviceScaleFactor=1, mobile=False)
    page.js("(() => { const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollTop = %d; })()" % y)
    time.sleep(0.6)


def make_video(frames, slow_spans, out: Path, gif: bool):
    """frames: (timestamp, jpg). slow_spans: (t0, t1) wall-clock spans to play SPEEDUP times faster."""
    if len(frames) < 2:
        print("too few frames for a video")
        return
    lst = out.with_suffix(".txt")
    lines = []
    for (t, p), (t2, _) in zip(frames, frames[1:] + [(frames[-1][0] + 2.0, None)]):
        d = max(t2 - t, 0.04)
        if any(a <= t < b for a, b in slow_spans):
            d /= SPEEDUP
        d = min(d, 2.5)            # a gap while a screenshot was taken (the screencast is paused then) is cut short
        lines.append("file '%s'\nduration %.3f" % (p.as_posix(), d))
    lines.append("file '%s'" % frames[-1][1].as_posix())
    lst.write_text("\n".join(lines), encoding="utf-8")
    vf = "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:white,fps=25,format=yuv420p" % (
        WIDTH, HEIGHT, WIDTH, HEIGHT)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", vf,
                    "-c:v", "libx264", "-crf", "26", "-preset", "slow", "-movflags", "+faststart", str(out)], check=True)
    lst.unlink()
    print("saved %s (%d bytes)" % (out, out.stat().st_size), flush=True)
    if gif:
        g = out.with_suffix(".gif")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-vf",
                        "fps=6,scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse",
                        str(g)], check=True)
        print("saved %s (%d bytes)" % (g, g.stat().st_size), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--video-name", default=None, help="default: frugal_<scenario>.mp4")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--gif", action="store_true")
    args = ap.parse_args()
    if not shutil.which("ffmpeg") and not args.no_video:
        raise SystemExit("ffmpeg is not on PATH")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="edge_rec_"))
    frames_dir = Path(tempfile.mkdtemp(prefix="frames_"))
    proc = subprocess.Popen([EDGE, "--headless=new", "--hide-scrollbars", "--remote-debugging-port=%d" % PORT,
                             "--user-data-dir=" + str(profile), "--window-size=%d,%d" % (WIDTH, HEIGHT),
                             "--autoplay-policy=no-user-gesture-required", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    slow = []
    try:
        page = Page(PORT)
        page.call("Page.enable")
        page.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=HEIGHT, deviceScaleFactor=1, mobile=False)

        def video(on: bool):
            if args.no_video:
                return
            if on:
                page.frame_dir = frames_dir
                page.call("Page.startScreencast", format="jpeg", quality=85, maxWidth=WIDTH, maxHeight=HEIGHT)
            else:
                page.call("Page.stopScreencast")
                page.frame_dir = None

        for step in SCENARIOS[args.scenario]:
            kind = step[0]
            print("step:", " ".join(str(s) for s in step).encode("ascii", "replace").decode(), flush=True)
            if kind == "goto":
                page.call("Page.navigate", url=args.url)
                time.sleep(2)
                video(True)
            elif kind == "click":
                click(page, step[1])
                time.sleep(0.8)
            elif kind == "wait":
                t0 = time.time()
                wait_text(page, step[1])
                slow.append((t0, time.time()))
            elif kind == "type":
                type_into(page, step[1], step[2] if len(step) > 2 else "textarea")
            elif kind == "pause":
                time.sleep(step[1])
            elif kind == "scroll":
                scroll_to(page, step[1], *step[2:])
                time.sleep(1.0)
            elif kind == "top":
                page.js("(() => { const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollTop = 0; })()")
            elif kind == "shot":
                p = out / (step[1] + ".png")
                view_shot(page, p)
                print("saved %s (%d bytes)" % (p, p.stat().st_size), flush=True)
            elif kind == "full":
                video(False)
                p = out / (step[1] + ".png")
                screenshot(page, p)
                print("saved %s (%d bytes)" % (p, p.stat().st_size), flush=True)
                video(True)
        video(False)
        page.ws.close()
    finally:
        proc.terminate()
    if not args.no_video:
        # screencast timestamps are wall-clock seconds, the same clock as time.time()
        make_video(page.frames, slow, out / (args.video_name or "frugal_%s.mp4" % args.scenario.replace("-", "")),
                   args.gif)
    shutil.rmtree(frames_dir, ignore_errors=True)
    shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
