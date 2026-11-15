import os from "node:os";

export function compatibility(manifest, platform = process.platform, release = os.release()) {
  const id = { linux: "orca", win32: "nvda", darwin: "voiceover" }[platform];
  const entry = manifest.screenReaders.find((r) => r.id === id);
  const major = release.split(".")[0];
  const asset = entry?.assets.find((a) => !a.platformVersion || a.platformVersion === major);
  return {
    platform, release, reader: id ?? null,
    assetCompatible: Boolean(asset), asset: asset ?? null,
    supportedPlatformVersions: entry?.assets.map((a) => a.platformVersion ?? "any") ?? [],
    installationVerified: false,
    reason: asset ? "版の条件は一致。実際の起動でインストールと設定を確認する。"
      : "インストールしたGuidepupのmanifestに対応する実行環境のアセットがない。",
  };
}

const READER_ACTIONS = new Set(["next", "previous", "nextHeading", "previousHeading", "nextLandmark",
  "previousLandmark", "nextLink", "previousLink", "act", "interact", "stopInteracting", "press", "type"]);

export function requireSharedDesktop(platform = process.platform, env = process.env) {
  if (platform === "linux" && (!env.DISPLAY || !env.DBUS_SESSION_BUS_ADDRESS)) {
    throw new Error("Orcaとブラウザーで同じDISPLAYとDBUS_SESSION_BUS_ADDRESSが必要。専用環境で xvfb-run -a dbus-run-session -- node scripts/screen_reader.mjs run … を実行する。");
  }
}

export function assertScope(url, request) {
  const allowed = request.allowed_origins ?? [new URL(request.url).origin];
  if (!allowed.includes(new URL(url).origin)) throw new Error("シナリオの範囲外へ移動した: " + new URL(url).origin);
}

export function validateRequest(request) {
  const url = new URL(request.url);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
    throw new Error("認証情報を含まないhttp/https URLを指定する");
  }
  if (typeof request.case_id !== "string" || !request.case_id.trim() || !Array.isArray(request.actions) || !request.actions.length) {
    throw new Error("case_idと具体的なactionsが必要");
  }
  if (request.allowed_origins !== undefined && (!Array.isArray(request.allowed_origins) ||
      !request.allowed_origins.length || request.allowed_origins.some((value) => {
        const parsed = new URL(value);
        return !["http:", "https:"].includes(parsed.protocol) || parsed.origin !== value;
      }))) throw new Error("allowed_originsは検証対象のhttp/httpsのorigin配列にする");
  assertScope(request.url, request);
  for (const a of request.actions) {
    if (typeof a.type !== "string" || a.type.split(".").length !== 2) throw new Error("操作名が不正");
    const [group, method] = a.type.split(".");
    if (!(group === "reader" && READER_ACTIONS.has(method)) &&
        !(group === "browser" && ["click", "fill", "press"].includes(method))) {
      throw new Error("許可されていない操作: " + a.type);
    }
    if (method === "press" && (typeof a.key !== "string" || !a.key.trim())) throw new Error("キー名が必要");
    if (["type", "fill"].includes(method) && typeof a.value !== "string") throw new Error("入力する値が必要");
    if (group === "browser" && method !== "press" &&
        !(typeof a.selector === "string" && a.selector.trim()) &&
        !(typeof a.role === "string" && typeof a.name === "string")) throw new Error("対象のselector又はroleとnameが必要");
    if (a.expect_contains !== undefined && (typeof a.expect_contains !== "string" || !a.expect_contains.trim())) {
      throw new Error("読み上げの期待値は空にしない");
    }
    if (a.expect_not_contains !== undefined && (!Array.isArray(a.expect_not_contains) || !a.expect_not_contains.length ||
        a.expect_not_contains.some((value) => typeof value !== "string" || !value.trim()))) {
      throw new Error("expect_not_containsは空でない文字列の配列にする");
    }
  }
  return request;
}

export function safeAction(a) {
  return Object.fromEntries(Object.entries(a).map(([k, v]) => [k, k === "value" ? "***" : v]));
}

export async function runActions(reader, page, actions, screenshot = async () => {}, request) {
  const observations = [];
  for (let i = 0; i < actions.length; i++) {
    const action = actions[i];
    if (request) assertScope(page.url(), request);
    const focus = async () => page.evaluate ? await page.evaluate(() => {
      const e = document.activeElement;
      return e ? { tag: e.localName, id: e.id, documentHasFocus: document.hasFocus(), text: (e.textContent ?? "").trim().slice(0, 200) } : null;
    }) : null;
    const focusBefore = await focus();
    await reader.clearSpokenPhraseLog();
    const [group, method] = action.type.split(".");
    let capture;
    if (group === "reader") {
      // Reader commands already serialize and capture. Nesting one inside
      // capture() would wait for a command queued behind its own capture.
      if (method === "press") await reader.press(action.key, { capture: true });
      else if (method === "type") await reader.type(action.value, { capture: true });
      else await reader[method]({ capture: true });
      capture = { spokenPhrase: await reader.lastSpokenPhrase(),
        itemText: reader.itemText ? await reader.itemText() : "" };
    } else {
      capture = await reader.capture(async () => {
        if (method === "press") return await page.keyboard.press(action.key);
        const locator = action.role
          ? page.getByRole(action.role, { name: action.name, exact: true })
          : page.locator(action.selector);
        if (method === "fill") return await locator.fill(action.value);
        return await locator.click();
      }, { capture: true });
    }
    const spokenPhrases = await reader.spokenPhraseLog();
    const combined = [capture.spokenPhrase, ...spokenPhrases].filter(Boolean).join("\n");
    const observation = {
      index: i + 1, action: safeAction(action), capture, spokenPhrases,
      expectedContains: action.expect_contains ?? null,
      expectedNotContains: action.expect_not_contains ?? [],
      assertion: action.expect_contains === undefined && action.expect_not_contains === undefined ? "not_requested"
        : (action.expect_contains === undefined || combined.includes(action.expect_contains)) &&
          (action.expect_not_contains ?? []).every((value) => !combined.includes(value)) ? "matched" : "not_matched",
      url: page.url(),
      focusBefore, focusAfter: await focus(),
    };
    observations.push(observation);
    await screenshot(i + 1, observation);
    if (request) assertScope(page.url(), request);
  }
  return observations;
}
