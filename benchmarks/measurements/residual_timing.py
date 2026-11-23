"""Measure bounded time-limit and draft-retention routes on the browser clock."""
from datetime import datetime, timezone
import re


CHECKPOINTS = {"2.2.1": "2.2.1-02", "2.2.6": "2.2.6-02"}
FIELDS = {"2.2.1": {"target", "start", "warning", "extend"}, "2.2.6": {"target", "save"}}
SELECTOR = re.compile(r"#[A-Za-z][A-Za-z0-9_-]*")
CLOCK_MODEL = "playwright-browser-clock"
BASE_TIME = datetime(2026, 11, 20, tzinfo=timezone.utc)
WARNING_MINIMUM_MS = 20_000
REQUIRED_EXTENSIONS = 10
MAX_LIMIT_OBSERVATION_MS = 120_000
HOUR_MS = 3_600_000
RETENTION_MINIMUM_MS = 20 * HOUR_MS + 1
RETENTION_TEST_MS = 21 * HOUR_MS
DRAFT = "Accessibility benchmark draft"

_TIMING_STATE = """({target, warning, extend}) => {
    const visible = node => node.checkVisibility({
        opacityProperty: true, visibilityProperty: true, contentVisibilityAuto: true
    });
    const read = () => {
        const elements = [target, warning, extend].map(selector => document.querySelectorAll(selector));
        if (elements.some(matches => matches.length !== 1)) throw new Error("Ambiguous timing target");
        const [input, alert, action] = elements.map(matches => matches[0]);
        return {
            at_ms: Date.now(), warning: visible(alert), editable: visible(input) && !input.readOnly && !input.matches(":disabled"),
            can_extend: visible(action) && !action.matches(":disabled") && action.getAttribute("aria-disabled") !== "true",
        };
    };
    const trace = [];
    const sample = () => {
        const current = read();
        const previous = trace.at(-1);
        if (!previous || current.warning !== previous.warning || current.editable !== previous.editable ||
            current.can_extend !== previous.can_extend) trace.push(current);
    };
    const watcher = new MutationObserver(sample);
    watcher.observe(document, {attributes: true, childList: true, subtree: true});
    sample();
    window.__wcagTimingObservation = {read, trace};
}"""


def validate_plan(criterion, plan):
    fields = FIELDS.get(criterion)
    if not fields or not isinstance(plan, dict) or set(plan) != fields:
        raise ValueError("Unsupported timing evidence plan")
    if any(not isinstance(value, str) or not SELECTOR.fullmatch(value) for value in plan.values()):
        raise ValueError("Timing evidence requires simple ID selectors")
    if len(set(plan.values())) != len(fields):
        raise ValueError("Timing evidence requires distinct controls")


async def setup(criterion, page, plan):
    validate_plan(criterion, plan)
    await page.clock.install(time=BASE_TIME)


async def _activate(page, selector):
    button = page.locator(selector)
    if await button.count() != 1 or not await button.is_visible() or not await button.is_enabled():
        return False
    await button.press("Enter", timeout=1500)
    return True


async def _begin_limit(page, plan):
    selectors = {name: plan[name] for name in ("target", "warning", "extend")}
    await page.evaluate(_TIMING_STATE, selectors)
    if not await _activate(page, plan["start"]):
        return None
    return await page.evaluate("() => window.__wcagTimingObservation.read()")


def _is_sample(sample):
    return (isinstance(sample, dict) and type(sample.get("at_ms")) is int
            and all(type(sample.get(key)) is bool for key in ("warning", "editable", "can_extend")))


def _limit_times(baseline):
    start = baseline.get("start")
    trace = baseline.get("trace")
    if not _is_sample(start) or not isinstance(trace, list) or not all(_is_sample(sample) for sample in trace):
        return None
    at = start["at_ms"]
    if not start["editable"] or start["warning"]:
        return None
    expiry_at = next((row["at_ms"] for row in trace if row["at_ms"] > at and not row["editable"]), None)
    if expiry_at is None:
        return None
    warning_at = next((row["at_ms"] for row in trace
                       if at < row["at_ms"] < expiry_at and row["warning"] and row["editable"]), None)
    if warning_at is None:
        return None
    return warning_at - at, expiry_at - at


async def _capture_extension(page, plan):
    start = await _begin_limit(page, plan)
    if start is None:
        return {}
    await page.clock.run_for(MAX_LIMIT_OBSERVATION_MS)
    trace = await page.evaluate("() => window.__wcagTimingObservation.trace")
    baseline = {"start": start, "trace": trace}
    evidence = {"baseline": baseline, "trials": []}
    times = _limit_times(baseline)
    if times is None:
        return evidence

    warning_offset, expiry_offset = times
    await page.reload(wait_until="load", timeout=4500)
    started = await _begin_limit(page, plan)
    if started is None:
        return evidence
    for _ in range(REQUIRED_EXTENSIONS):
        now = await page.evaluate("() => Date.now()")
        until_warning = started["at_ms"] + warning_offset - now
        if until_warning > 0:
            await page.clock.run_for(until_warning)
        before = await page.evaluate("() => window.__wcagTimingObservation.read()")
        if not before["can_extend"] or not before["editable"] or not before["warning"]:
            break
        if not await _activate(page, plan["extend"]):
            break
        after = await page.evaluate("() => window.__wcagTimingObservation.read()")
        until_old_expiry = started["at_ms"] + expiry_offset + 1 - after["at_ms"]
        if until_old_expiry <= 0:
            break
        await page.clock.run_for(until_old_expiry)
        at_old_expiry = await page.evaluate("() => window.__wcagTimingObservation.read()")
        evidence["trials"].append({
            "timer_start_ms": started["at_ms"], "before": before, "after": after, "at_old_expiry": at_old_expiry
        })
        if not at_old_expiry["editable"] or after["warning"]:
            break
        started = after
    return evidence


async def _retention_recheck(page, plan, elapsed):
    draft = page.locator(plan["target"])
    if await draft.count() != 1 or not await draft.is_visible() or not await draft.is_editable():
        return {}
    url = page.url
    marker = f"{DRAFT} {elapsed}"
    await draft.fill(marker, timeout=1500)
    if not await _activate(page, plan["save"]):
        return {}
    save_at = await page.evaluate("() => Date.now()")
    await page.reload(wait_until="load", timeout=4500)
    if page.url != url or await draft.count() != 1 or not await draft.is_visible():
        return {}
    initial_at = await page.evaluate("() => Date.now()")
    initial_matches = await draft.input_value(timeout=1500) == marker
    if not initial_matches:
        return {"initial_matches": False}
    now = await page.evaluate("() => Date.now()")
    await page.clock.fast_forward(save_at + elapsed - now)
    await page.reload(wait_until="load", timeout=4500)
    if page.url != url or await draft.count() != 1 or not await draft.is_visible():
        return {}
    value = await draft.input_value(timeout=1500)
    return {
        "save_at_ms": save_at, "initial_at_ms": initial_at, "initial_matches": True,
        "final_at_ms": await page.evaluate("() => Date.now()"),
        "value": "same" if value == marker else "blank" if not value else "other",
    }


async def _capture_retention(page, plan):
    return {"rechecks": [await _retention_recheck(page, plan, elapsed)
                        for elapsed in (RETENTION_MINIMUM_MS, RETENTION_TEST_MS)]}


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    now = await page.evaluate("() => Date.now()")
    await page.clock.pause_at(now + 1000)
    original_url = page.url
    if criterion == "2.2.1":
        measured = await _capture_extension(page, plan)
    else:
        measured = await _capture_retention(page, plan)
    if page.url != original_url:
        return {}
    return {"clock": CLOCK_MODEL, **measured}


def _trial_result(trial, warning_offset, expiry_offset):
    start = trial["timer_start_ms"]
    before = trial["before"]
    after = trial["after"]
    at_expiry = trial["at_old_expiry"]
    if not all(_is_sample(sample) for sample in (before, after, at_expiry)):
        return None
    if (type(start) is not int or before["at_ms"] != start + warning_offset
            or not before["editable"] or not before["warning"]
            or not before["can_extend"] or before["at_ms"] != after["at_ms"]
            or at_expiry["at_ms"] != start + expiry_offset + 1):
        return None
    if at_expiry["editable"] is False:
        return False
    if after["warning"] is False and after["editable"] is True:
        return True
    return None


def _evaluate_extension(evidence):
    times = _limit_times(evidence.get("baseline", {}))
    if times is None:
        return "cant_tell", "仮想時計で警告と編集期限の順序を確認できませんでした。"
    warning_offset, expiry_offset = times
    notice = expiry_offset - warning_offset
    count = 0
    exhausted = False
    timer_start = None
    for trial in evidence.get("trials", []):
        if timer_start is not None and timer_start != trial["timer_start_ms"]:
            break
        result = _trial_result(trial, warning_offset, expiry_offset)
        if result is not True:
            exhausted = result is False
            break
        timer_start = trial["after"]["at_ms"]
        count += 1
    observed = f"仮想時計で警告から編集期限まで{notice / 1000:g}秒を測定。延長後に旧期限を越えて編集できた回数は{count}回。"
    if notice < WARNING_MINIMUM_MS or (exhausted and count < REQUIRED_EXTENSIONS):
        return "failed", observed
    if count >= REQUIRED_EXTENSIONS:
        return "passed", observed
    return "cant_tell", observed


def _verified_recheck(result, elapsed):
    saved = result.get("save_at_ms")
    initial = result.get("initial_at_ms")
    final = result.get("final_at_ms")
    return (all(type(value) is int for value in (saved, initial, final))
            and 0 <= initial - saved <= 1000 and final - saved == elapsed
            and result.get("initial_matches") is True)


def _evaluate_retention(evidence):
    rechecks = evidence.get("rechecks")
    if (not isinstance(rechecks, list) or len(rechecks) != 2
            or not all(isinstance(row, dict) and _verified_recheck(row, elapsed)
                       for row, elapsed in zip(rechecks, (RETENTION_MINIMUM_MS, RETENTION_TEST_MS)))):
        return "cant_tell", "保存直後の復元と仮想時間の経過を確認できませんでした。"
    values = [row.get("value") for row in rechecks]
    if values == ["same", "same"]:
        return "passed", "保存直後と仮想時計で21時間経過後の再読み込みで、同じ下書きを復元できました。"
    if values == ["blank", "blank"]:
        return "failed", "保存直後は下書きを復元できましたが、仮想時計で20時間を超えた直後と21時間後は空欄でした。"
    return "cant_tell", "仮想時計の再読み込みで、20時間を超えた直後と21時間後の保持をともに確認できませんでした。"


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    outcome = "cant_tell"
    observed = "ブラウザーの仮想時計による計測を確認できませんでした。"
    if isinstance(evidence, dict) and evidence.get("clock") == CLOCK_MODEL:
        try:
            outcome, observed = (_evaluate_extension(evidence) if criterion == "2.2.1"
                                 else _evaluate_retention(evidence))
        except (KeyError, TypeError):
            observed = "仮想時計の証拠に必要な観測値がありません。"
    return [{"target": plan["target"], "checkpoint": CHECKPOINTS[criterion],
             "outcome": outcome, "observed": observed}]
