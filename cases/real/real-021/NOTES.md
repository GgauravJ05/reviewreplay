# real-021 (hono-49ce5376)

Source: [honojs/hono](https://github.com/honojs/hono), MIT licence, Copyright (c) 2021 - present, Yusuke Wada and Hono contributors.

Introduced in `49ce5376846bc7eba14104764cfbbe71ea809a3a`: refactor(compress-middleware): resolve type assertion using const assertion (#1343)
Fixed in `f0ed2465913f2a89ebdf65cc54d6254915fc3ff6`: fix(compress): respect Accept-Encoding when encoding option is set (#4951)

Why this is a bug:
The compress middleware read the request's Accept-Encoding header and bailed out when the
configured encoding was not accepted. This refactor replaced that check with
`options?.encoding ?? ENCODING_TYPES.find(...)`. As soon as an `encoding` option is set, the
nullish-coalescing operator short-circuits and the header is never consulted, so the middleware
compresses every response with that encoding. A client that advertises only deflate, or sends no
Accept-Encoding at all, still receives `Content-Encoding: gzip` and cannot decode the body.

The fix message says: "When the encoding option is set, the middleware previously compressed
responses unconditionally, regardless of the Accept-Encoding header. This could send a response
in an encoding the client cannot decode". The fix adds `selectEncoding()`, which parses
Accept-Encoding (q-values, wildcard, case) even when an encoding is configured, and adds tests
that expect no Content-Encoding when the configured encoding is not accepted.

The same line is duplicated in `deno_dist/middleware/compress/index.ts`; both copies are listed
in the answer key.

How it was picked: `reviewreplay mine` on honojs/hono (multi-language miner). The fix message
does not name the introducing commit, so the signal is blame only: `git blame` of the line the
fix rewrites points at 49ce5376. Signals: message reference=False, blame agrees=True.

No third-party code was run; the evidence is the two diffs and the fix's message.
