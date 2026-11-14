# real-013 (axios-cabead53)

Source: [axios/axios](https://github.com/axios/axios), MIT licence, Copyright (c) 2014-present Matt Zabriskie & Collaborators.

Introduced in `163da7226fd2cd21f0f238f99b2f75a51bf9b2a3`: fix: update the implementation to rather parse out the values than throw (#10687)
Fixed in `cabead530614ec86761d92d81af2783aafeb9d01`: fix: preserve Unicode headers for request interceptors (#10850)
Issue: https://github.com/axios/axios/issues/10849 ("V1.16.0 custom request header attributes do not support Chinese")

Why this is a bug:
Before this commit, `AxiosHeaders` threw on CR/LF in a header value and otherwise kept the value
as given, Unicode included. This commit replaced the throw with sanitising at set time:
`normalizeValue` now runs `sanitizeHeaderValue`, which deletes every character outside
`\x09\x20-\x7E\x80-\xFF`. A header such as `X-Name: 请求用户` becomes an empty string the moment it
is stored, before request interceptors run, so they can no longer read or encode it.

The fix keeps non-control Unicode in `AxiosHeaders` (stripping only C0 controls and DEL at set
time) and sanitises to byte strings in each adapter (`http.js`, `xhr.js`, `fetch.js`) just before
the request is sent. Its new tests in `tests/unit/axiosHeaders.test.js` check that `'请求用户'`,
`'naïve'` and `'プロジェクト'` round-trip through `set`/`get`.

How it was picked: mined with `reviewreplay mine` (language-aware miner, PR #16). The miner named
`163da722` from `git blame`; I read the fix, the introducing diff and its parent by hand and
confirmed the stripping first appears in this commit. Signals: message reference=False; one
blamed commit, so `agree` is not set.

No third-party code was run; the evidence is the fix commit, its tests and the linked issue.

Note: the introducing commit also changes `lib/helpers/shouldBypassProxy.js` (loopback names
treated as equal). That change is not the bug; it is listed in `related_valid`.
