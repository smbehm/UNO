# Little Boutique Productions

Private film prompt studio at `/little-boutique-productions`. Describe a scene, answer adaptive questions, refine direction, and copy individual Higgsfield clips or download a prompt pack. Defaults to Uno, stylized feature animation, 30 seconds, and 16:9. Film and style are editable for any production.

## Configuration

Add Production secrets in Vercel: `OPENAI_API_KEY`, `LBP_PASSWORD` (16+ characters), and `LBP_SESSION_SECRET` (32+ random characters). Optionally configure `OPENAI_MODEL`; default is `gpt-6-astra`. API model access and billing must be enabled for that project. Redeploy after changing environment variables. Never commit actual credentials.

The route serves a password gate; API requests require a signed, eight-hour HttpOnly session and same-origin JSON requests. Changing the password or session secret invalidates existing sessions. Pages carry noindex and no-store headers and are absent from site navigation and sitemap. This is a shared studio password, not individual user accounts.

Rate limits are best-effort per server instance, not a durable global spending cap. Set API project budget alerts and monitor usage; configure Vercel Firewall rate limits for stronger public endpoint protection. Do not treat alerts as hard spending caps.

Drafts stay in sessionStorage in the current browser tab. Submitted scene text, reference descriptions, and answers go to OpenAI for direction. No images or video are uploaded here; bind actual references in Higgsfield. Responses use store:false; provider retention policies still apply. No scene database is created.

## Development and validation

Node 22 or newer. Run `npm test`. For local use, set environment variables in the shell or an ignored `.env` file and run `node --env-file=.env dev.cjs`. Visit `http://127.0.0.1:4173/little-boutique-productions`. The local server only serves studio routes, not the existing UNO homepage.

Tests cover authentication, signed-cookie tampering, password rotation, cross-origin protection, validation, basic throttling, structured API requests, and upstream errors using fixtures. Live model access must also be checked after deployment.

The reviewed universal film instructions live in `lib/guide.cjs`; `lib/director.cjs` adds the web output contract. Capability claims must be periodically reviewed against Higgsfield documentation. A requested 30-second scene may require multiple clips; final prompts are direction, not a guarantee of render quality.
