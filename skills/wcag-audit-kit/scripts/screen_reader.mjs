#!/usr/bin/env node
import { readFile, writeFile, mkdir, access } from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import os from "node:os";
import { compatibility, validateRequest, runActions, requireSharedDesktop, assertScope, safeAction } from "./screen_reader_core.mjs";

const require = createRequire(import.meta.url);
const args = process.argv.slice(2);
const command = args.shift();
const option = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
let output;
let result = { status: "blocked", observations: [], environment: { platform: process.platform, release: os.release() } };
let reader;
let browser;
let startAttempted = false;
let code = 2;

try {
  const main = require.resolve("@guidepup/guidepup");
  let packageRoot = path.dirname(main);
  while (true) {
    try { await access(path.join(packageRoot, "manifest.json")); break; }
    catch { const parent = path.dirname(packageRoot); if (parent === packageRoot) throw new Error("Guidepup manifestが見つからない"); packageRoot = parent; }
  }
  const manifest = JSON.parse(await readFile(path.join(packageRoot, "manifest.json"), "utf8"));
  const pkg = JSON.parse(await readFile(path.join(packageRoot, "package.json"), "utf8"));
  const doctor = { ...compatibility(manifest), guidepupVersion: pkg.version, nodeVersion: process.version,
    simulation: false, note: "Virtual Screen Readerは使わない。対応判定だけで起動済み・読み上げ確認済みとはしない。" };
  result.environment = doctor;
  if (command === "doctor") {
    console.log(JSON.stringify(doctor, null, 2));
    process.exitCode = doctor.assetCompatible ? 0 : 2;
  } else {
    if (command !== "run" || !option("--request") || !option("--out")) {
      throw new Error("使い方: screen_reader.mjs doctor | run --request request.json --out <空の証拠ディレクトリー>");
    }
    const destination = path.resolve(option("--out"));
    try { await access(destination); throw new Error("証拠ディレクトリーは新しい場所にする"); }
    catch (e) { if (e.code !== "ENOENT") throw e; }
    await mkdir(destination, { recursive: true });
    output = destination;
    const requestText = await readFile(path.resolve(option("--request")), "utf8");
    const request = validateRequest(JSON.parse(requestText));
    result = { ...result, case_id: request.case_id,
      request_sha256: createHash("sha256").update(requestText).digest("hex"), started_at: new Date().toISOString(),
      scenario: { url: request.url, allowed_origins: request.allowed_origins ?? [new URL(request.url).origin],
        actions: request.actions.map(safeAction) },
      expectedNote: "読み上げの部分一致は検査1件の観察結果。WCAG基準全体の判定は別に行う。" };
    if (!doctor.assetCompatible) throw new Error(doctor.reason);
    requireSharedDesktop();
    const guidepup = await import("@guidepup/guidepup");
    reader = guidepup[{ orca: "orca", nvda: "nvda", voiceover: "voiceOver" }[doctor.reader]];
    startAttempted = true;
    await reader.start({ capture: true });
    result.environment.readerName = reader.name;
    result.environment.readerVersion = reader.version;
    result.environment.installationVerified = true;
    // On Linux the caller supplies one dedicated X/D-Bus session so that
    // both Guidepup and the browser inherit the same desktop.
    const { chromium, firefox, webkit } = await import("playwright-core");
    const engines = { chromium, firefox, webkit };
    const browserName = request.browser ?? (process.platform === "darwin" ? "webkit" : "chromium");
    if (!engines[browserName]) throw new Error("未知のブラウザー");
    browser = await engines[browserName].launch({ headless: false,
      ...(request.executablePath ? { executablePath: request.executablePath } : {}),
      ...(browserName === "chromium" && process.platform === "linux" ? { args: ["--force-renderer-accessibility"] } : {}) });
    const context = await browser.newContext({ viewport: request.viewport ?? { width: 1280, height: 900 } });
    const page = await context.newPage();
    await page.goto(request.url, { waitUntil: "domcontentloaded" });
    assertScope(page.url(), request);
    await page.bringToFront();
    result.environment.browser = browserName;
    result.environment.browserVersion = browser.version();
    await page.screenshot({ path: path.join(output, "before.png"), fullPage: true });
    result.observations = await runActions(reader, page, request.actions, async (i, observation) => {
      result.observations.push(observation);
      await page.screenshot({ path: path.join(output, `step-${i}.png`), fullPage: true });
      await writeFile(path.join(output, `step-${i}.json`), JSON.stringify(observation, null, 2));
    }, request);
    result.status = result.observations.some((o) => o.assertion === "not_matched") ? "assertion_failed" : "collected";
    code = result.status === "collected" ? 0 : 1;
  }
} catch (error) {
  result.error = error.message;
  if (!output) console.error(error.message);
  process.exitCode = 2;
} finally {
  if (browser) await browser.close().catch((e) => { result.browser_cleanup_error = e.message; });
  if (startAttempted) await reader.stop().catch((e) => { result.reader_cleanup_error = e.message; });
  if (result.reader_cleanup_error || result.browser_cleanup_error) { result.status = "blocked"; code = 2; }
  if (output) {
    result.finished_at = new Date().toISOString();
    await writeFile(path.join(output, "screen-reader.json"), JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ status: result.status, error: result.error, evidence: output }, null, 2));
    process.exitCode = code;
  } else if (command !== "doctor") process.exitCode = code;
}
