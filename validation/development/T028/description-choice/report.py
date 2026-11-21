"""Attach the observation to ordinary after-select cases and check their reports."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

from openpyxl import load_workbook

from analyze import digest, load, speech_has_code
from observe import HERE, REPO, start_server, write_json

CLI = REPO / "skills/wcag-audit-kit/scripts/audit.py"
REMAINING = "選択した受付コード以外の映像や非言語音の情報と、別の再生環境での結果は未確認。"


def cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *map(str, args)],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"audit.py {args[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def configured_case(output, folder, observation, page_url, asset):
    actions = load(folder / "keyboard.json")
    select = next(i for i, action in enumerate(actions) if action["press"] == "Enter")
    config_file = output / f"{folder.name}-config.json"
    config = {
        "schema_version": "1", "url": page_url, "level": "AA",
        "scope": {"include": [urlsplit(page_url).path]},
        "environments": [{"id": "desktop", "viewport": {"width": 1280, "height": 900}, "zoom": 1}],
        "keyboard_steps": 0,
        "states": [{
            "id": "after-select", "paths": [urlsplit(page_url).path],
            "actions": [{"type": "press", "key": item["press"]} for item in actions[:select + 1]],
            "assert": [
                {"selector": '#describe[aria-pressed="true"]', "text": "音声解説を使う"},
                {"selector": f'#subject[src="{asset}"]'},
            ],
        }],
    }
    write_json(config_file, config)
    ledger = output / folder.name
    cli("page", "--url", page_url, "--out", ledger, "--config", config_file, "--mode", "ai")
    plan = load(ledger / "work/plan.json")
    case, = [case for case in plan["cases"]
             if case["criterion"] == "1.2.5" and case["state"] == "after-select"
             and case["page_url"] == page_url and case["environment"] == "desktop"]
    assert case["capture_execution"] == "completed" and case["assessment"] is None, case
    state = load(ledger / "work" / case["evidence_dir"] / "inventory.json")
    media, = [item for item in state["nodes"] if item["selector"] == "#subject"]
    assert media["src"] == asset and media["visible"]
    assert observation["states"][1]["state"]["url"] == page_url
    assert observation["states"][1]["state"]["src"] == asset
    return ledger, case


def attach_and_record(output, ledger, case, evidence, model_observation, observed):
    case_id = case["case_id"]
    info = json.loads(cli("case", "--run", ledger, "--id", case_id))
    refs = []
    for path in evidence:
        reference = cli("attach", "--run", ledger, "--case", case_id, "--file", path)
        attached = ledger / "work" / reference
        assert digest(attached) == digest(path)
        refs.append(reference)
    delivered = model_observation["playedSrc"]
    outcome = "passed" if case["page_url"].endswith("/p04.html") else "failed"
    case_outcome = "failed" if outcome == "failed" else "cant_tell"
    expected = "音声解説を選んで再生した音声から、画面の受付コード7291が分かる。"
    interval = {
        "start": 0, "end": model_observation["duration"], "status": "reviewed",
        "observed": observed, "expected": expected, "evidence": refs,
    }
    record = {
        "case_id": case_id, "base_assessment": None, "outcome": case_outcome,
        "config_digest": info["config_digest"],
        "normative_sha256": info["criterion"]["normative_sha256"],
        "execution": "completed", "observed": observed,
        "coverage_complete": False, "remaining": [REMAINING],
        "tests_applied": ["1.2.5-01 / 音声解説の選択と再生された音声"],
        "steps_executed": [
            "TabとEnterで音声解説を選択する。",
            "Shift+Tabで再生ボタンに戻り、Spaceで最初から終端まで再生する。",
            "配信された動画とブラウザーで再生した音声を、受付コードの表示と照合する。",
        ],
        "evidence": refs,
        "targets": [{
            "target": "#subject / 1.2.5-01 / 受付コード7291",
            "outcome": outcome, "observed": observed, "expected": expected, "evidence": refs,
            "media_review": {
                "source": delivered, "timeline": "prerecorded", "duration": model_observation["duration"],
                "comparison": "全区間の音声と画面の受付コード1件の照合。",
                "intervals": [interval],
            },
        }],
    }
    record_file = output / f"{ledger.name}-record.json"
    write_json(record_file, record)
    cli("record", "--run", ledger, "--file", record_file)
    cli("page-report", "--run", ledger, "--page-exact", case["page_url"])
    return verify_reports(ledger, case_id, record, refs)


def verify_reports(ledger, case_id, record, refs):
    reports = ("data/report.json", "reports/report.html", "reports/report.xlsx", "reports/details/issues.md")
    report = load(ledger / reports[0])
    row, = [item for item in report["cases"] if item["case_id"] == case_id]
    assert row["state"] == "after-select" and row["outcome"] == record["outcome"]
    assessment = row["assessment_data"]
    assert not assessment["coverage_complete"] and not report["audit_complete"]
    assert assessment["targets"] == record["targets"] and assessment["remaining"] == record["remaining"]
    html = (ledger / reports[1]).read_text()
    assert record["observed"] in html and all(Path(path).name in html for path in refs)
    assert REMAINING in html
    issues = (ledger / reports[3]).read_text()
    assert (record["observed"] in issues) == (record["outcome"] == "failed")
    book = load_workbook(ledger / reports[2], read_only=True)
    try:
        for sheet, outcome in (("検査票", record["outcome"]), ("対象", record["targets"][0]["outcome"])):
            rows = iter(book[sheet].values)
            headers = next(rows)
            line, = [dict(zip(headers, row)) for row in rows if row[0] == case_id]
            assert line["判定"] == outcome and line["観察"] == record["observed"]
    finally:
        book.close()
    return {
        "case_id": case_id, "state": "after-select", "criterion": "1.2.5",
        "criterion_outcome": record["outcome"], "aspect": "1.2.5-01",
        "aspect_outcome": record["targets"][0]["outcome"], "attachments": refs,
        "files_sha256": {path: digest(ledger / path) for path in reports},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    conditions = load(HERE / "conditions.json")
    environment = load(args.run / "environment.json")
    proof = args.run / "decode/corroboration.json"
    audio = load(proof)
    assert audio["sameDecodedVideoFrameHashes"]
    origin = environment["origin"]
    fixture_dir = REPO / conditions["fixture_root"]
    fixture = {}
    for path, expected in conditions["fixtures_sha256"].items():
        assert digest(fixture_dir / path) == expected
        fixture[path] = (fixture_dir / path).read_bytes()
    args.out.mkdir()
    port = urlsplit(origin).port
    server, thread, _ = start_server(fixture, port)
    try:
        results = {}
        for condition in conditions["conditions"]:
            if not condition["select"]:
                continue
            ident = condition["id"]
            folder = args.run / ident
            observation = load(folder / "observation.json")
            match = audio["conditions"][ident]
            source = urlsplit(match["playedSrc"]).path.lstrip("/")
            includes_code = speech_has_code(match["browserAudio"])
            assert includes_code == condition["expected_code_in_audio"]
            if includes_code:
                observed = "選択後の動画は開始から終端まで再生され、再生音声に画面の受付コード7291が含まれた。"
            else:
                observed = "音声解説の選択表示に変わった後も元動画が終端まで再生され、画面の受付コード7291は再生音声に含まれなかった。"
            paths = [folder / name for name in ("keyboard.json", "observation.json",
                                                "playing-03.0.png", "played-audio.webm")]
            paths.extend([proof, proof.with_name("key-dispatch.json")])
            url = f"{origin}/{condition['page']}"
            ledger, case = configured_case(args.out, folder, observation, url, source)
            results[ident] = attach_and_record(args.out, ledger, case, paths, match, observed)
            print(ident, results[ident], flush=True)
        write_json(args.out / "report-checks.json", results)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


if __name__ == "__main__":
    main()
