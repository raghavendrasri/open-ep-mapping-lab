// Tests for the feedback Worker. Every outside call (Turnstile, GitHub) is mocked, so these run offline.
// Run: node --test test/*.test.js   (tests/test_feedback.py runs them as part of pytest)
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import worker, { KINDS, LIMITS, buildIssue, cleanTitle, fence, validate } from "../src/index.js";

const SITE = "https://openepengineering.org/";
const ORIGIN = "https://openepengineering.org";
const ENV = {
  SITE_URL: SITE,
  ALLOWED_ORIGINS: ORIGIN,
  EXPECTED_HOSTNAME: "openepengineering.org",
  GITHUB_REPO: "owner/repo",
  GITHUB_TOKEN: "test-token-not-real",
  TURNSTILE_SECRET: "test-secret-not-real",
};

const good = () => ({
  kind: "error",
  message: "The bipolar figure caption says 2 mm but the text says 4 mm.",
  page: "https://openepengineering.org/modules/m03-electrograms.html?x=1#fig-2",
  pageTitle: "m03 · Electrograms – Open EP Mapping Lab",
  selection: "spacing of 4 mm",
  token: "XXXX.DUMMY.TOKEN.XXXX",
  website: "",
});

let calls;
let turnstileAnswer;
let githubStatus;
const realFetch = globalThis.fetch;

beforeEach(() => {
  calls = [];
  turnstileAnswer = { success: true, hostname: "openepengineering.org" };
  githubStatus = 201;
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init });
    if (String(url).startsWith("https://challenges.cloudflare.com/")) {
      return new Response(JSON.stringify(turnstileAnswer), { headers: { "Content-Type": "application/json" } });
    }
    if (String(url).startsWith("https://api.github.com/")) {
      const body = githubStatus === 201 ? { html_url: "https://github.com/owner/repo/issues/7", number: 7 } : { message: "Bad credentials" };
      return new Response(JSON.stringify(body), { status: githubStatus, headers: { "Content-Type": "application/json" } });
    }
    throw new Error(`unexpected fetch to ${url}`);
  };
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

function post(payload, { origin = ORIGIN, env = ENV, raw } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (origin) headers.Origin = origin;
  const req = new Request("https://feedback.openepengineering.org/", {
    method: "POST",
    headers,
    body: raw ?? JSON.stringify(payload),
  });
  return worker.fetch(req, env);
}

// ---------------------------------------------------------------- happy path

test("valid feedback creates one GitHub issue and returns its address", async () => {
  const res = await post(good());
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, url: "https://github.com/owner/repo/issues/7", number: 7 });
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), ORIGIN);

  assert.equal(calls.length, 2);
  const [verify, create] = calls;
  assert.equal(verify.url, "https://challenges.cloudflare.com/turnstile/v0/siteverify");
  assert.equal(verify.init.body.get("secret"), ENV.TURNSTILE_SECRET);
  assert.equal(verify.init.body.get("response"), "XXXX.DUMMY.TOKEN.XXXX");
  assert.equal(verify.init.body.get("remoteip"), null, "the reader's IP address is not sent anywhere");

  assert.equal(create.url, "https://api.github.com/repos/owner/repo/issues");
  assert.equal(create.init.headers.Authorization, "Bearer test-token-not-real");
  assert.equal(create.init.headers["X-GitHub-Api-Version"], "2026-03-10");
  assert.ok(create.init.headers["User-Agent"]);
  const issue = JSON.parse(create.init.body);
  assert.equal(issue.title, "Feedback (Error in the content): modules/m03-electrograms");
  assert.equal(issue.labels, undefined, "labels come from the label-feedback workflow");
  assert.match(issue.body, /https:\/\/openepengineering\.org\/modules\/m03-electrograms\.html\n/);
  assert.ok(!issue.body.includes("?x=1") && !issue.body.includes("#fig-2"), "query and fragment are dropped");
  assert.ok(issue.body.includes("spacing of 4 mm"));
  assert.ok(!issue.body.includes("XXXX.DUMMY"), "the spam-check token is not posted");
});

test("dry run returns the issue without calling GitHub", async () => {
  const res = await post(good(), { env: { ...ENV, DRY_RUN: "1", GITHUB_TOKEN: "" } });
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.dryRun, true);
  assert.equal(data.issue.title, "Feedback (Error in the content): modules/m03-electrograms");
  assert.equal(calls.filter((c) => c.url.startsWith("https://api.github.com/")).length, 0);
});

// ---------------------------------------------------------------- refusals

test("other websites cannot use the relay", async () => {
  const res = await post(good(), { origin: "https://evil.example" });
  assert.equal(res.status, 403);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), null);
  assert.equal(calls.length, 0);
});

test("preflight answers only the course site", async () => {
  const ok = await worker.fetch(new Request("https://f.test/", { method: "OPTIONS", headers: { Origin: ORIGIN } }), ENV);
  assert.equal(ok.status, 204);
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  const other = await worker.fetch(new Request("https://f.test/", { method: "OPTIONS", headers: { Origin: "https://x.test" } }), ENV);
  assert.equal(other.headers.get("Access-Control-Allow-Origin"), null);
});

test("failed spam check creates nothing", async () => {
  turnstileAnswer = { success: false, "error-codes": ["invalid-input-response"] };
  const res = await post(good());
  assert.equal(res.status, 403);
  assert.equal(calls.filter((c) => c.url.startsWith("https://api.github.com/")).length, 0);
});

test("a token issued for another hostname is refused", async () => {
  turnstileAnswer = { success: true, hostname: "elsewhere.example" };
  assert.equal((await post(good())).status, 403);
});

test("filled honeypot field is refused before any outside call", async () => {
  const res = await post({ ...good(), website: "http://spam.example" });
  assert.equal(res.status, 403);
  assert.equal(calls.length, 0);
});

test("bad input is refused before any outside call", async () => {
  const cases = [
    [{ ...good(), kind: "praise" }, "bad-kind"],
    [{ ...good(), message: "short" }, "message-too-short"],
    [{ ...good(), message: "x".repeat(LIMITS.messageMax + 1) }, "message-too-long"],
    [{ ...good(), page: "https://evil.example/modules/m03.html" }, "bad-page"],
    [{ ...good(), page: "not a url" }, "bad-page"],
    [{ ...good(), token: "" }, "spam-check"],
  ];
  for (const [payload, error] of cases) {
    const res = await post(payload);
    assert.ok(res.status === 400 || res.status === 403, error);
    assert.equal((await res.json()).error, error);
  }
  assert.equal((await post(null, { raw: "{not json" })).status, 400);
  assert.equal((await post(null, { raw: "x".repeat(LIMITS.requestBytes + 1) })).status, 413);
  assert.equal(calls.length, 0);
});

test("GitHub failure is reported without leaking details", async () => {
  githubStatus = 401;
  const res = await post(good());
  assert.equal(res.status, 502);
  assert.deepEqual(await res.json(), { error: "github-failed" });
});

test("missing secrets are reported as not configured", async () => {
  const res = await post(good(), { env: { ...ENV, GITHUB_TOKEN: undefined } });
  assert.equal(res.status, 500);
  assert.equal(calls.length, 0);
});

// ---------------------------------------------------------------- what reaches the issue

test("reader text cannot break out of its code fence, mention people or add links", () => {
  const nasty = "~~~~~\n@raghavendrasri see [x](https://evil.example)\n~~~~~~~";
  const checked = validate({ ...good(), message: nasty, selection: "@someone" }, SITE);
  assert.ok(checked.ok);
  const issue = buildIssue(checked.value);
  const f = fence(nasty);
  assert.equal(f, "~".repeat(8));
  assert.ok(issue.body.includes(`${f}text\n${nasty}\n${f}`));
  // Outside the two fenced blocks, nothing the reader typed appears.
  const outside = issue.body.replace(`${f}text\n${nasty}\n${f}`, "").replace("~~~~text\n@someone\n~~~~", "");
  assert.ok(!outside.includes("~~~~"), "both fenced blocks were found and removed");
  assert.ok(!outside.includes("@raghavendrasri") && !outside.includes("evil.example"));
});

test("page titles are flattened to plain text and shown as inline code", () => {
  assert.equal(cleanTitle("[click](https://x) <b>@me</b> **m03** `x`"), "click(https://x) bme/b m03 x");
  const v = validate({ ...good(), pageTitle: "Visit https://spam.example `now`" }, SITE).value;
  assert.ok(buildIssue(v).body.includes("**Page:** `Visit https://spam.example now` https://openepengineering.org/"));
});

test("titles name the page without any reader text", () => {
  const home = validate({ ...good(), page: "https://openepengineering.org/" }, SITE).value;
  assert.equal(buildIssue(home).title, "Feedback (Error in the content): home page");
  const glossary = validate({ ...good(), kind: "unclear", page: "https://openepengineering.org/glossary/index.html" }, SITE).value;
  assert.equal(buildIssue(glossary).title, "Feedback (Something is unclear): glossary/");
});

test("every kind has a label", () => {
  for (const kind of Object.keys(KINDS)) assert.ok(validate({ ...good(), kind }, SITE).ok);
});
