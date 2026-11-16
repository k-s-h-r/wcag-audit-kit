import { test } from "node:test";
import assert from "node:assert/strict";
import { compatibility, validateRequest, runActions, requireSharedDesktop, assertScope } from "../skills/wcag-audit-kit/scripts/screen_reader_core.mjs";

const manifest = { screenReaders: [
  { id: "orca", assets: [{ platformVersion: "7", version: "test" }] },
  { id: "nvda", assets: [{ version: "test" }] },
  { id: "voiceover", assets: [{ platformVersion: "24", version: "test" }] },
] };

test("OSを検出しただけで対応済みにしない", () => {
  const value = compatibility(manifest, "linux", "6.18.57");
  assert.equal(value.reader, "orca");
  assert.equal(value.assetCompatible, false);
  assert.equal(value.installationVerified, false);
  assert.equal(compatibility(manifest, "linux", "7.0").assetCompatible, true);
});
test("WindowsとmacOSは対応するアセットで判定する", () => {
  assert.equal(compatibility(manifest, "win32", "10.0").assetCompatible, true);
  assert.equal(compatibility(manifest, "darwin", "24.6").assetCompatible, true);
  assert.equal(compatibility(manifest, "darwin", "20.0").assetCompatible, false);
});
test("仮想読み上げや任意の関数を検査アクションにしない", () => {
  assert.throws(() => validateRequest({ url: "https://example.com", case_id: "a", actions: [{ type: "reader.stop" }] }));
  assert.throws(() => validateRequest({ url: "https://example.com", case_id: "a", actions: [{ type: "virtual.next" }] }));
});
test("LinuxのOrcaとブラウザーには共有する専用セッションが必要", () => {
  assert.throws(() => requireSharedDesktop("linux", {}));
  assert.throws(() => requireSharedDesktop("linux", { DISPLAY: ":99" }));
  assert.doesNotThrow(() => requireSharedDesktop("linux", { DISPLAY: ":99", DBUS_SESSION_BUS_ADDRESS: "unix:path=/tmp/test-bus" }));
  assert.doesNotThrow(() => requireSharedDesktop("win32", {}));
});
test("別originへの移動や不正な操作指定を拒否する", () => {
  const request = { url: "https://example.com", case_id: "a", actions: [{ type: "browser.press", key: "Tab" }] };
  validateRequest(request);
  assert.throws(() => assertScope("https://other.example/", request));
  assert.throws(() => validateRequest({ ...request, actions: [{ type: "browser.press.extra", key: "Tab" }] }));
  assert.throws(() => validateRequest({ ...request, actions: [{ type: "browser.click" }] }));
  assert.throws(() => validateRequest({ ...request, actions: [{ type: "reader.type" }] }));
});
test("前の読み上げをクリアし、空の出力を期待どおりにしない", async () => {
  const calls = [];
  const reader = {
    clearSpokenPhraseLog: async () => calls.push("clear"),
    capture: async () => { throw new Error("reader操作をcaptureで包んではいけない"); },
    press: async (key) => calls.push(key),
    lastSpokenPhrase: async () => "",
    spokenPhraseLog: async () => [],
  };
  const results = await runActions(reader, { url: () => "https://example.com" }, [
    { type: "reader.press", key: "Space", expect_contains: "Saved" },
  ]);
  assert.deepEqual(calls, ["clear", "Space"]);
  assert.equal(results[0].assertion, "not_matched");
});
test("出力と期待値が一致してもWCAG合格は作らない", async () => {
  const reader = { clearSpokenPhraseLog: async () => {},
    capture: async () => { throw new Error("reader操作をcaptureで包んではいけない"); },
    lastSpokenPhrase: async () => "Saved successfully.",
    act: async () => {}, spokenPhraseLog: async () => ["Saved successfully."] };
  const [result] = await runActions(reader, { url: () => "https://example.com" }, [
    { type: "reader.act", expect_contains: "Saved" },
  ]);
  assert.equal(result.assertion, "matched");
  assert.equal("wcag_passed" in result, false);
});
test("外部ブラウザー操作はcapture中に実行して発話を取得する", async () => {
  const calls = [];
  const reader = { clearSpokenPhraseLog: async () => calls.push("clear"),
    capture: async (action, options) => { calls.push(options); await action(); return { spokenPhrase: "Saved" }; },
    spokenPhraseLog: async () => ["Saved"] };
  const page = { url: () => "https://example.com/", keyboard: { press: async (key) => calls.push(key) } };
  const [result] = await runActions(reader, page, [{ type: "browser.press", key: "Space", expect_contains: "Saved" }]);
  assert.deepEqual(calls, ["clear", { capture: true }, "Space"]);
  assert.equal(result.assertion, "matched");
});

test("not checkedをcheckedの成功として扱わない", async () => {
  const reader = { clearSpokenPhraseLog: async () => {}, act: async () => {},
    lastSpokenPhrase: async () => "not checked", spokenPhraseLog: async () => ["not checked"] };
  const [result] = await runActions(reader, { url: () => "https://example.com" }, [{
    type: "reader.act", expect_contains: "checked", expect_not_contains: ["not checked", "unchecked"],
  }]);
  assert.equal(result.assertion, "not_matched");
});
