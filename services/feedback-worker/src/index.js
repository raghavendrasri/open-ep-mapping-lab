// Open EP Mapping Lab: feedback relay (Cloudflare Worker).
//
// The site's Feedback form (assets/feedback.html) posts here. The Worker checks the input, verifies the
// Cloudflare Turnstile spam check and opens an issue in the course repository. The GitHub token and the
// Turnstile secret are Worker secrets: nothing secret lives in the repository or in the page.
//
// What is stored: the kind of feedback, the message, the page address and title, and any text the reader
// chose to quote, all in a public GitHub issue. No name, email or IP address is collected.
//
// Setup and deployment: services/feedback-worker/README.md. Tests: services/feedback-worker/test/,
// run by tests/test_feedback.py (they mock every network call, so CI stays offline).

export const KINDS = {
  error: "Error in the content",
  unclear: "Something is unclear",
  broken: "Broken page or demo",
  suggestion: "Suggestion",
  other: "Other",
};

export const LIMITS = {
  messageMin: 10,
  messageMax: 4000,
  selectionMax: 1000,
  pageTitleMax: 150,
  tokenMax: 2048,
  requestBytes: 20000,
};

export const GITHUB_API_VERSION = "2026-03-10";
export const SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

// Control characters except tab and newline.
const CONTROL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g;

function cleanText(value) {
  return String(value).replace(/\r\n?/g, "\n").replace(CONTROL, "").trim();
}

// Page titles go into the issue as plain text: drop characters Markdown would act on (links, emphasis,
// tables, HTML, @mentions) and collapse whitespace.
export function cleanTitle(value) {
  return cleanText(value)
    .replace(/[\[\]<>@`*_|\\#]/g, "")
    .replace(/\s+/g, " ")
    .slice(0, LIMITS.pageTitleMax)
    .trim();
}

// A code fence longer than any run of tildes in the text, so reader text can never close it. Inside a fence,
// Markdown, links and @mentions are shown as typed and do not notify anyone.
export function fence(text) {
  const longest = Math.max(0, ...(String(text).match(/~+/g) || []).map((run) => run.length));
  return "~".repeat(Math.max(4, longest + 1));
}

function fenced(text) {
  const f = fence(text);
  return `${f}text\n${text}\n${f}`;
}

// Returns { ok: true, value } or { ok: false, error }.
export function validate(input, siteUrl) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return { ok: false, error: "bad-request" };
  if (input.website) return { ok: false, error: "spam-check" }; // hidden field that people never fill in
  if (!Object.hasOwn(KINDS, input.kind)) return { ok: false, error: "bad-kind" };

  const message = typeof input.message === "string" ? cleanText(input.message) : "";
  if (message.length < LIMITS.messageMin) return { ok: false, error: "message-too-short" };
  if (message.length > LIMITS.messageMax) return { ok: false, error: "message-too-long" };

  let page;
  try {
    page = new URL(String(input.page));
  } catch {
    return { ok: false, error: "bad-page" };
  }
  const site = new URL(siteUrl);
  if (page.origin !== site.origin) return { ok: false, error: "bad-page" };

  let selection = typeof input.selection === "string" ? cleanText(input.selection) : "";
  if (selection.length > LIMITS.selectionMax) selection = selection.slice(0, LIMITS.selectionMax) + " …";

  const token = typeof input.token === "string" ? input.token : "";
  if (!token || token.length > LIMITS.tokenMax) return { ok: false, error: "spam-check" };

  return {
    ok: true,
    value: {
      kind: input.kind,
      message,
      selection,
      pageUrl: page.origin + page.pathname, // no query string or fragment
      pagePath: page.pathname,
      pageTitle: cleanTitle(input.pageTitle || ""),
      token,
    },
  };
}

export function buildIssue(value, labels = ["feedback"]) {
  const shortPath = value.pagePath.replace(/^\/+/, "").replace(/\.html$/, "").replace(/(^|\/)index$/, "$1") || "home page";
  const title = `Feedback (${KINDS[value.kind]}): ${shortPath}`;
  // The title comes from the reader's browser, so it is shown as inline code: no links, mentions or markup.
  const pageLine = value.pageTitle ? `\`${value.pageTitle}\` ${value.pageUrl}` : value.pageUrl;
  const parts = [
    `**Kind:** ${KINDS[value.kind]}`,
    `**Page:** ${pageLine}`,
    "",
    "**Feedback**",
    "",
    fenced(value.message),
  ];
  if (value.selection) parts.push("", "**Text the reader selected on the page**", "", fenced(value.selection));
  parts.push(
    "",
    "---",
    "Sent with the Feedback button on the course site. The sender is anonymous: the form collects no name, " +
      "email or IP address. Please check the claim against its source before changing the course.",
  );
  return { title, body: parts.join("\n"), labels };
}

export async function verifyTurnstile(token, secret, expectedHostname) {
  const form = new FormData();
  form.append("secret", secret);
  form.append("response", token);
  const res = await fetch(SITEVERIFY_URL, { method: "POST", body: form });
  const outcome = await res.json();
  if (!outcome.success) return false;
  if (expectedHostname && outcome.hostname !== expectedHostname) return false;
  return true;
}

export async function createIssue(env, issue) {
  const res = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/issues`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "open-ep-mapping-lab-feedback",
      "X-GitHub-Api-Version": GITHUB_API_VERSION,
    },
    body: JSON.stringify(issue),
  });
  if (!res.ok) {
    console.error(`GitHub answered ${res.status} when creating a feedback issue`);
    return null;
  }
  const data = await res.json();
  return { url: data.html_url, number: data.number };
}

function allowedOrigins(env) {
  return String(env.ALLOWED_ORIGINS || "")
    .split(",")
    .map((o) => o.trim())
    .filter(Boolean);
}

function corsHeaders(origin, env) {
  const headers = { Vary: "Origin" };
  if (origin && allowedOrigins(env).includes(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Methods"] = "POST, OPTIONS";
    headers["Access-Control-Allow-Headers"] = "Content-Type";
    headers["Access-Control-Max-Age"] = "86400";
  }
  return headers;
}

function json(status, payload, headers) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...headers, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin");
    const cors = corsHeaders(origin, env);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method === "GET") {
      return new Response("Open EP Mapping Lab feedback relay. The site's Feedback form posts here.\n", {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }
    if (request.method !== "POST") return json(405, { error: "method-not-allowed" }, cors);
    if (!cors["Access-Control-Allow-Origin"]) return json(403, { error: "origin-not-allowed" }, cors);

    const dryRun = env.DRY_RUN === "1";
    if (!env.TURNSTILE_SECRET || (!dryRun && (!env.GITHUB_TOKEN || !env.GITHUB_REPO)) || !env.SITE_URL) {
      return json(500, { error: "not-configured" }, cors);
    }

    const text = await request.text();
    if (text.length > LIMITS.requestBytes) return json(413, { error: "too-large" }, cors);
    let input;
    try {
      input = JSON.parse(text);
    } catch {
      return json(400, { error: "bad-request" }, cors);
    }

    const checked = validate(input, env.SITE_URL);
    if (!checked.ok) return json(checked.error === "spam-check" ? 403 : 400, { error: checked.error }, cors);

    let human;
    try {
      human = await verifyTurnstile(checked.value.token, env.TURNSTILE_SECRET, env.EXPECTED_HOSTNAME);
    } catch {
      return json(503, { error: "spam-check-unavailable" }, cors);
    }
    if (!human) return json(403, { error: "spam-check" }, cors);

    const labels = String(env.ISSUE_LABELS || "feedback").split(",").map((l) => l.trim()).filter(Boolean);
    const issue = buildIssue(checked.value, labels);
    if (dryRun) return json(200, { ok: true, dryRun: true, issue }, cors);

    let created;
    try {
      created = await createIssue(env, issue);
    } catch {
      created = null;
    }
    if (!created) return json(502, { error: "github-failed" }, cors);
    return json(201, { ok: true, url: created.url, number: created.number }, cors);
  },
};
