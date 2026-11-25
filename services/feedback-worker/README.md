# Feedback relay (Cloudflare Worker)

The **Feedback** button on every course page opens a short form. This Worker receives the form, checks
it, verifies the spam check (Cloudflare Turnstile) and opens an issue in the course repository with the
label `feedback`. Readers do not need a GitHub account.

Until the Worker is deployed and switched on in `assets/feedback.html`, the button still works: it
opens a prefilled issue on GitHub, which the reader submits with their own GitHub account.

## What is sent and stored

- **Posted publicly as a GitHub issue:** the kind of feedback, the message, the page address and title,
  and any text the reader selected and chose to include.
- **Not collected:** name, email or IP address. The form warns readers not to include personal or
  patient information.
- Reader text is shown in code blocks in the issue, so it cannot add links or @mention anyone. The
  issue title is built only from the kind of feedback and the page path.

## One-time setup (about 15 minutes)

You do these steps yourself, because they create credentials. Never paste the token or the secret key
into a file in this repository, a chat or an issue.

1. **GitHub token.** Go to GitHub → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token.
   - Repository access: **Only select repositories** → `open-ep-mapping-lab`.
   - Repository permissions: **Issues → Read and write**. Leave everything else at "No access".
   - Pick an expiry date and put a reminder in your calendar to renew it.
2. **Spam check.** In the Cloudflare dashboard, open **Turnstile** → **Add widget**.
   - Hostname: `openepengineering.org`. Widget mode: Managed.
   - Note the **site key** (public) and the **secret key** (private).
3. **Deploy the Worker** from this folder (needs Node.js installed):

   ```sh
   cd services/feedback-worker
   npx wrangler login                      # opens Cloudflare in the browser
   npx wrangler deploy                     # creates feedback.openepengineering.org
   npx wrangler secret put GITHUB_TOKEN    # paste the GitHub token when asked
   npx wrangler secret put TURNSTILE_SECRET  # paste the Turnstile secret key when asked
   ```

   `wrangler.toml` holds the public settings: the site address, the repository and the label.
4. **Switch the form on.** In `assets/feedback.html`, set the two public values and open a pull
   request:

   ```js
   endpoint: "https://feedback.openepengineering.org/",
   turnstileSiteKey: "<the site key from step 2>",
   ```

5. **Try it.** On the live site, send a test message from any page. An issue labeled `feedback` should
   appear in the repository within a few seconds. Close it afterwards.

## Day-to-day

- **Watch the Worker's log:** `npx wrangler tail` (shows failures such as an expired token).
- **Renew the token:** create a new one as in step 1, then run `npx wrangler secret put GITHUB_TOKEN` again.
- **Turn the automatic form off:** set `endpoint: ""` in `assets/feedback.html`. The button goes back
  to opening a prefilled GitHub issue.
- **Spam:** every submission must pass Turnstile, and each Turnstile token works only once. If spam
  still gets through, add a Cloudflare rate-limiting rule for `feedback.openepengineering.org`.

## Testing

- `node --test test/*.test.js` runs the Worker tests with every outside call mocked (no network, no
  token). `pytest` runs them too, through `tests/test_feedback.py`.
- To try the Worker locally without creating issues, create `.dev.vars` in this folder (it is in
  `.gitignore`) with Cloudflare's public test secret, which always passes, and dry-run mode:

  ```sh
  TURNSTILE_SECRET=1x0000000000000000000000000000000AA
  EXPECTED_HOSTNAME=
  DRY_RUN=1
  ```

  Then run `npx wrangler dev` and, in a second terminal, send a test message to the address it prints
  (the token below is Cloudflare's test token):

  ```sh
  curl -s -X POST http://localhost:8787/ \
    -H "Origin: https://openepengineering.org" -H "Content-Type: application/json" \
    -d '{"kind":"other","message":"Testing the feedback relay.","page":"https://openepengineering.org/","token":"XXXX.DUMMY.TOKEN.XXXX"}'
  ```

  In dry-run mode, the Worker returns the issue it would have created instead of calling GitHub.
