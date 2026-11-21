"""Observe the stock 1.2.5 fixtures with a real Chromium keyboard and player."""
import argparse
import base64
import hashlib
import json
import mimetypes
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

OBSERVERS = """
(() => {
  if (window !== window.top) return;
  const records = [];
  const describe = e => e instanceof Element ? {
    tag: e.tagName, id: e.id, text: e.id === 'describe' ? e.innerText : '',
    pressed: e.getAttribute('aria-pressed'), label: e.getAttribute('aria-label')
  } : null;
  function record(event) {
    records.push({
      type: event.type, isTrusted: event.isTrusted, key: event.key ?? null,
      code: event.code ?? null, shift: event.shiftKey ?? null,
      detail: event.detail ?? null,
      target: describe(event.target),
      focus: describe(document.activeElement),
      t: performance.now(), eventTime: event.timeStamp,
      currentSrc: document.querySelector('video')?.currentSrc ?? '',
      currentTime: document.querySelector('video')?.currentTime ?? null
    });
  }
  for (const event of ['keydown', 'keyup', 'click', 'play', 'playing', 'pause',
      'ended', 'seeking', 'seeked', 'loadstart', 'loadedmetadata',
      'loadeddata', 'volumechange', 'ratechange', 'error']) {
    window.addEventListener(event, record, {capture: true, passive: true});
  }
  window.t028ObservedEvents = records;
})();
"""

STATE = """
() => {
  const video = document.querySelector('video');
  const choice = document.querySelector('#describe');
  const quality = video.getVideoPlaybackQuality();
  return {
    clock: performance.now(), url: location.href,
    focus: {tag: document.activeElement.tagName, id: document.activeElement.id},
    button: {name: choice.innerText, pressed: choice.getAttribute('aria-pressed')},
    currentSrc: video.currentSrc, src: video.getAttribute('src'),
    currentTime: video.currentTime, duration: video.duration,
    readyState: video.readyState, paused: video.paused, ended: video.ended,
    muted: video.muted, volume: video.volume, playbackRate: video.playbackRate,
    played: [...Array(video.played.length)].map((_, i) => [
      video.played.start(i), video.played.end(i)
    ]),
    videoQuality: {
      total: quality.totalVideoFrames, dropped: quality.droppedVideoFrames
    }
  };
}
"""

CAPTURE_AUDIO = """
() => {
  const video = document.querySelector('video');
  const stream = video.captureStream();
  const tracks = stream.getAudioTracks();
  if (tracks.length !== 1) throw Error('Expected one audio track from captureStream');
  const audio = new MediaStream(tracks);
  const recorder = new MediaRecorder(audio, {mimeType: 'audio/webm;codecs=opus'});
  const chunks = [];
  const startedAt = performance.now();
  const mediaStartTime = video.currentTime;
  const result = new Promise((resolve, reject) => {
    recorder.onerror = event => reject(event.error);
    recorder.ondataavailable = event => chunks.push(event.data);
    recorder.onstop = () => {
      const reader = new FileReader();
      reader.onerror = () => reject(reader.error);
      reader.onload = () => resolve({
        base64: reader.result.split(',')[1], mimeType: recorder.mimeType,
        audioTrackSettings: tracks[0].getSettings(), startedAt,
        stoppedAt: performance.now(), mediaStartTime, mediaEndTime: video.currentTime
      });
      reader.readAsDataURL(new Blob(chunks, {type: recorder.mimeType}));
    };
  });
  recorder.start();
  window.t028AudioCapture = {recorder, result};
}
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def start_server(fixture, port=0):
    receipts = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path.lstrip("/")
            if path not in fixture:
                self.send_error(404)
                return
            data = fixture[path]
            size = len(data)
            start, end = 0, size - 1
            range_header = self.headers.get("Range")
            if range_header:
                bounds = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
                if not bounds:
                    self.send_error(416)
                    return
                start = int(bounds[1])
                end = min(end, int(bounds[2]) if bounds[2] else end)
                if start > end:
                    self.send_error(416)
                    return
            body = data[start:end + 1]
            status = 206 if range_header else 200
            with lock:
                receipt = {
                    "id": str(len(receipts) + 1), "path": path,
                    "range": range_header, "status": status, "start": start,
                    "endInclusive": end, "totalLength": size, "length": len(body),
                    "bodySha256": digest(body), "resourceSha256": digest(data),
                    "sent": False,
                }
                receipts.append(receipt)
            self.send_response(status)
            self.send_header("Content-Type", mimetypes.guess_type(path)[0])
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-T028-Receipt", receipt["id"])
            if range_header:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                return
            receipt["sent"] = True

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, receipts


def focused(tree):
    results = []
    for node in tree["nodes"]:
        properties = {item["name"]: item["value"].get("value") for item in node.get("properties", [])}
        if properties.get("focused") and not node["ignored"]:
            results.append({
                "role": node["role"]["value"],
                "name": node.get("name", {}).get("value", ""),
                "pressed": properties.get("pressed"),
            })
    return results


def observe(browser, condition, origin, folder, viewport):
    folder.mkdir()
    context = browser.new_context(
        viewport={"width": viewport[0], "height": viewport[1]},
        device_scale_factor=1, locale="en-US", service_workers="block",
    )
    context.route("**/*", lambda route: (
        route.continue_() if route.request.url.startswith(origin + "/") else route.abort()
    ))
    context.add_init_script(OBSERVERS)
    page = context.new_page()
    session = context.new_cdp_session(page)
    session.send("Accessibility.enable")
    session.send("Network.enable")
    network = []
    for name in ("requestWillBeSent", "responseReceived", "loadingFinished", "loadingFailed"):
        session.on(f"Network.{name}", lambda event, name=name: network.append({
            "event": name, "data": event
        }))
    actions = []
    screenshots = []

    def snapshot(step):
        tree = session.send("Accessibility.getFullAXTree")
        write_json(folder / f"{step}-aria.json", tree)
        return {"step": step, "state": page.evaluate(STATE), "axFocus": focused(tree)}

    def screenshot(name, sample=None):
        before = page.evaluate(STATE)
        page.screenshot(path=folder / f"{name}.png")
        after = page.evaluate(STATE)
        screenshots.append({
            "file": f"{name}.png", "sample": sample,
            "beforeTime": before["currentTime"], "afterTime": after["currentTime"],
        })

    def press(key):
        pre = page.evaluate("window.t028ObservedEvents.length")
        page.keyboard.press(key)
        if key == "Space":
            page.wait_for_function("() => !document.querySelector('video').paused")
        state = page.evaluate(STATE)
        ax = focused(session.send("Accessibility.getFullAXTree"))
        events = page.evaluate("start => window.t028ObservedEvents.slice(start)", pre)
        keyboard = [event for event in events if event["type"] in ("keydown", "keyup")]
        actions.append({"press": key, "after": state, "axFocus": ax, "events": events})
        assert all(event["isTrusted"] for event in keyboard)
        if key == "Enter":
            assert any(event["key"] == key and event["isTrusted"] for event in keyboard)
        return ax

    def tab_to(key, names):
        for _ in range(12):
            ax = press(key)
            if any(node["role"] == "button" and node["name"].casefold() in names for node in ax):
                return
        raise RuntimeError(f"Keyboard focus did not reach {sorted(names)}. Focus: {ax}")

    try:
        response = page.goto(origin + "/" + condition["page"], wait_until="load")
        assert response.status == 200
        page.wait_for_function("document.querySelector('video').readyState >= 2")
        initial = snapshot("initial")
        screenshot("initial")
        if condition["select"]:
            tab_to("Tab", {"音声解説を使う"})
            press("Enter")
            page.wait_for_function("document.querySelector('video').readyState >= 2")
            selected = snapshot("after-select")
            screenshot("after-select")
            tab_to("Shift+Tab", {"play", "play video", "再生"})
        else:
            selected = None
            tab_to("Tab", {"play", "play video", "再生"})
        before_play = snapshot("before-play")
        assert before_play["state"]["currentTime"] == 0
        assert not before_play["state"]["muted"]
        assert before_play["state"]["playbackRate"] == 1
        page.evaluate(CAPTURE_AUDIO)
        press("Space")
        duration = before_play["state"]["duration"]
        for sample in [0.5, *range(1, int(duration) + 1)]:
            if sample >= duration - 0.15:
                continue
            page.wait_for_function(
                "t => document.querySelector('video').currentTime >= t", arg=sample
            )
            screenshot(f"playing-{sample:04.1f}", sample)
        page.wait_for_function("document.querySelector('video').ended")
        ended = snapshot("ended")
        audio = page.evaluate("""async () => {
          const capture = window.t028AudioCapture;
          capture.recorder.stop();
          return await capture.result;
        }""")
        audio_bytes = base64.b64decode(audio.pop("base64"))
        (folder / "played-audio.webm").write_bytes(audio_bytes)
        audio["sha256"] = digest(audio_bytes)
        screenshot("ended")
        states = [initial, selected, before_play, ended]
        write_json(folder / "observation.json", {
            "condition": condition["id"], "states": states, "capture": audio,
            "screenshots": screenshots,
        })
        print(condition["id"], selected and selected["state"]["button"],
              ended["state"]["currentSrc"], ended["state"]["played"],
              f"captured {len(audio_bytes)} audio bytes", flush=True)
    finally:
        if page.url.startswith(origin + "/"):
            write_json(folder / "events.json", page.evaluate("window.t028ObservedEvents"))
        write_json(folder / "keyboard.json", actions)
        write_json(folder / "network.json", network)
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    plan_path = HERE / "conditions.json"
    plan = json.loads(plan_path.read_text())
    fixture_root = REPO / plan["fixture_root"]
    fixture = {path: (fixture_root / path).read_bytes() for path in plan["fixtures_sha256"]}
    assert all(digest(data) == plan["fixtures_sha256"][path] for path, data in fixture.items())
    args.run.mkdir(parents=True)
    server, thread, receipts = start_server(fixture)
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=args.chromium, headless=True,
                ignore_default_args=["--mute-audio"],
            )
            write_json(args.run / "environment.json", {
                "utc": datetime.now(timezone.utc).isoformat(), "origin": origin,
                "chromium": browser.version, "fixtureSha256": plan["fixtures_sha256"],
                "planSha256": digest(plan_path.read_bytes()),
            })
            for condition in plan["conditions"]:
                observe(browser, condition, origin, args.run / condition["id"],
                        plan["browser"]["viewport_css_px"])
            browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        write_json(args.run / "server-receipts.json", receipts)


if __name__ == "__main__":
    main()
