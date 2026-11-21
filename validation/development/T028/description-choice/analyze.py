"""Cross-check browser delivery and decode both the resource and played audio."""
import argparse
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path
from urllib.parse import urlsplit

from observe import HERE, REPO, write_json


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command, log):
    result = subprocess.run(command, capture_output=True, text=True)
    log.append({
        "command": [str(arg) for arg in command],
        "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
    })
    result.check_returncode()
    return result.stdout


def inspect_audio(path, output, args, log):
    wav = output.with_suffix(".wav")
    execute(["ffmpeg", "-nostdin", "-v", "error", "-threads", "1", "-i", path, "-map", "0:a:0",
             "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav], log)
    execute([args.whisper, "-m", args.model, "-f", wav, "-l", "en",
             "-ng", "-t", "2", "-oj", "-of", output], log)
    transcript = load(output.with_suffix(".json"))
    with wave.open(str(wav)) as audio:
        wav_duration = audio.getnframes() / audio.getframerate()
    return {
        "input": str(path), "inputSha256": digest(path), "wav": wav.name,
        "wavSha256": digest(wav), "wavDuration": wav_duration,
        "whisper": output.with_suffix(".json").name,
        "transcription": transcript["transcription"],
    }


def media_receipts(network, receipts, url, resource):
    by_id = {record["id"]: record for record in receipts if record["sent"]}
    finished = {
        entry["data"]["requestId"]: entry["data"]["encodedDataLength"]
        for entry in network if entry["event"] == "loadingFinished"
    }
    matches = []
    for entry in network:
        if entry["event"] != "responseReceived":
            continue
        data = entry["data"]
        response = data["response"]
        if response["url"] != url or data["type"] != "Media" or data["requestId"] not in finished:
            continue
        headers = {name.lower(): value for name, value in response["headers"].items()}
        receipt = by_id[headers["x-t028-receipt"]]
        assert not response.get("fromDiskCache") and not response.get("fromServiceWorker")
        assert receipt["resourceSha256"] == digest(resource)
        body = resource.read_bytes()[receipt["start"]:receipt["endInclusive"] + 1]
        assert receipt["bodySha256"] == hashlib.sha256(body).hexdigest()
        assert int(headers["content-length"]) == len(body)
        assert response["status"] == receipt["status"]
        encoded_length = finished[data["requestId"]]
        assert encoded_length >= len(body)
        matches.append({
            "requestId": data["requestId"], "browserResponseStatus": response["status"],
            "browserContentRange": headers.get("content-range"), "browserEncodedLength": encoded_length,
            "serverReceipt": receipt,
        })
    covered = 0
    for record in sorted(matches, key=lambda match: match["serverReceipt"]["start"]):
        receipt = record["serverReceipt"]
        assert receipt["start"] <= covered, "Gap in received media ranges"
        covered = max(covered, receipt["endInclusive"] + 1)
    assert covered == resource.stat().st_size, "Browser receipts do not cover the complete resource"
    return matches


def keyboard_protocol(path, plan, run):
    sends = {}
    navigations = {}
    acknowledgments = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if " SEND ► " in line:
            message = json.loads(line.split(" SEND ► ", 1)[1])
            if message["method"] == "Input.dispatchKeyEvent":
                sends.setdefault(message["sessionId"], []).append(message)
            if message["method"] == "Page.navigate":
                navigations[message["sessionId"]] = message
        elif " ◀ RECV " in line:
            message = json.loads(line.split(" ◀ RECV ", 1)[1])
            if "id" in message:
                acknowledgments[message.get("sessionId"), message["id"]] = message
    results = {}
    origin = load(run / "environment.json")["origin"]
    for condition, (session, messages) in zip(plan["conditions"], sends.items(), strict=True):
        navigation = navigations[session]
        assert navigation["params"]["url"] == f"{origin}/{condition['page']}"
        observed = load(run / condition["id"] / "keyboard.json")
        primary = [message["params"] for message in messages
                   if message["params"]["code"] not in ("ShiftLeft", "ShiftRight")]
        assert len(primary) == 2 * len(observed)
        for action, down, up in zip(observed, primary[::2], primary[1::2], strict=True):
            key = action["press"].split("+")[-1]
            assert down["code"] == up["code"] == key
            assert down["type"] in ("rawKeyDown", "keyDown") and up["type"] == "keyUp"
        responses = [acknowledgments[session, message["id"]] for message in messages]
        assert all("result" in acknowledgment for acknowledgment in responses)
        results[condition["id"]] = {
            "navigation": navigation, "commands": messages, "acknowledgments": responses,
        }
    return results


def speech_text(audio):
    return " ".join(part["text"].strip() for part in audio["transcription"])


def speech_has_code(audio):
    return bool(re.search(r"(?<!\d)7[\s-]*2[\s-]*9[\s-]*1(?!\d)", speech_text(audio)))


def verify_playback(folder, expected_pressed):
    observation = load(folder / "observation.json")
    initial, selected, before, ending = observation["states"]
    start = before["state"]
    end = ending["state"]
    assert initial["state"]["button"]["pressed"] == "false"
    assert end["button"]["pressed"] == expected_pressed
    if selected:
        assert selected["state"]["button"]["pressed"] == "true"
    assert start["currentSrc"] == end["currentSrc"]
    assert start["currentTime"] == 0 and end["ended"] and end["currentTime"] == end["duration"]
    assert end["played"] == [[0, end["duration"]]]
    assert end["videoQuality"]["total"] > 0
    assert end["playbackRate"] == 1 and end["volume"] == 1 and not end["muted"]
    actions = load(folder / "keyboard.json")
    if selected:
        activation, = [action for action in actions if action["press"] == "Enter"]
        events = [event for event in activation["events"]
                  if event["type"] in ("keydown", "keyup", "click")]
        assert [event["type"] for event in events] == ["keydown", "click", "keyup"]
        assert all(event["isTrusted"] and event["focus"]["id"] == "describe"
                   and event["target"]["id"] == "describe" for event in events)
        assert events[0]["key"] == events[2]["key"] == "Enter" and events[1]["detail"] == 0
    play, = [action for action in actions if action["press"] == "Space"]
    assert any(item["role"] == "button" and item["name"].casefold() == "play"
               for item in before["axFocus"])
    assert not play["after"]["paused"]
    events = load(folder / "events.json")
    assert all(any(event["type"] == kind and event["isTrusted"] for event in events)
               for kind in ("play", "playing", "ended"))
    assert not any(event["type"] in ("seeking", "seeked", "ratechange", "volumechange", "error")
                   for event in events)
    capture = observation["capture"]
    assert capture["mediaStartTime"] == 0 and capture["mediaEndTime"] == end["duration"]
    return initial["state"], end, capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--whisper", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    plan = load(HERE / "conditions.json")
    assert digest(args.model) == plan["analysis_tools"]["whisper_model_sha256"]
    assert load(args.run / "environment.json")["planSha256"] == digest(HERE / "conditions.json")
    fixture = REPO / plan["fixture_root"]
    receipts = load(args.run / "server-receipts.json")
    output = args.out or args.run / "decode"
    output.mkdir()
    write_json(output / "key-dispatch.json", keyboard_protocol(args.protocol, plan, args.run))
    commands = []
    resources = {}
    results = {}

    try:
        ffmpeg = execute(["ffmpeg", "-version"], commands).splitlines()[0]
        whisper_source = digest(args.whisper)
        for condition in plan["conditions"]:
            ident = condition["id"]
            folder = args.run / ident
            initial, end, capture = verify_playback(folder, "true" if condition["select"] else "false")
            path = urlsplit(end["currentSrc"]).path.lstrip("/")
            expected = condition["expected_delivery"]
            assert path == f"assets/expanded-{expected}.webm", path
            resource = fixture / path
            assert digest(resource) == plan["fixtures_sha256"][path]
            network = load(folder / "network.json")
            source = fixture / "assets/expanded-source.webm"
            assert urlsplit(initial["currentSrc"]).path == "/assets/expanded-source.webm"
            initial_receipts = media_receipts(network, receipts, initial["currentSrc"], source)
            finished_receipts = media_receipts(network, receipts, end["currentSrc"], resource)
            asset_id = resource.stem
            if path not in resources:
                raw_audio = inspect_audio(resource, output / asset_id, args, commands)
                framehash = output / f"{asset_id}.framehash"
                execute(["ffmpeg", "-nostdin", "-v", "error", "-threads", "1", "-i", resource,
                         "-map", "0:v:0", "-pix_fmt", "rgba", "-threads", "1",
                         "-f", "framehash", "-hash", "sha256", framehash],
                        commands)
                resources[path] = {"audio": raw_audio, "videoFrames": framehash.name,
                                   "frameSha256": digest(framehash)}
            captured_audio = folder / "played-audio.webm"
            assert capture["sha256"] == digest(captured_audio)
            played = inspect_audio(captured_audio, output / f"{ident}-played", args, commands)
            assert abs(played["wavDuration"] - end["duration"]) <= 0.25
            assert speech_has_code(played) == condition["expected_code_in_audio"]
            assert speech_has_code(played) == speech_has_code(resources[path]["audio"])
            results[ident] = {
                "initialSrc": initial["currentSrc"], "initialMediaReceipts": initial_receipts,
                "playedSrc": end["currentSrc"],
                "playedFromTo": end["played"], "duration": end["duration"],
                "mediaReceipts": finished_receipts, "browserAudio": played,
            }
            print(ident, end["currentSrc"], speech_text(played), flush=True)
        frames = [resources[path]["frameSha256"] for path in resources]
        handles = {
            "ffmpeg": ffmpeg, "whisperBinarySha256": whisper_source,
            "modelSha256": digest(args.model), "conditions": results, "resources": resources,
            "sameDecodedVideoFrameHashes": len(frames) == 2 and len(set(frames)) == 1,
        }
        write_json(output / "corroboration.json", handles)
    finally:
        write_json(output / "commands.json", commands)


if __name__ == "__main__":
    main()
