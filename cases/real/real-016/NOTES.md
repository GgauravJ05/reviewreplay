# real-016 (axios-822e3e40)

Source: [axios/axios](https://github.com/axios/axios), MIT licence, Copyright (c) 2014-present Matt Zabriskie & Collaborators.

Introduced in `1c6a86dd2c0623ee1af043a8491dbc96d40e883b`: fix: turn AxiosError into a native error (#5394) (#5558)
Fixed in `822e3e40b4f9287b5a787f5d1dfb3ae7f8a0faa3`: fix: make AxiosError.message property enumerable (#7392)

Why this is a bug:
Before this commit `AxiosError` was a function constructor that set `this.message = message`, an
ordinary enumerable property. This commit made it `class AxiosError extends Error` and passed the
message to `super(message)`. The native `Error` constructor defines `message` as non-enumerable,
so `Object.keys`, `Object.entries`, object spread and `for...in` no longer see it. Code that
copies or logs errors that way loses the message without any error.

The fix message says: "In v1.13.3, the refactoring to extend native Error made message
non-enumerable, breaking code that uses Object.keys(), Object.entries(), or spread operator on
AxiosError instances", and names "Breaking change introduced in: v1.13.3 (commit 1c6a86d)". It
redefines `message` with `Object.defineProperty(..., {enumerable: true})`.

The same commit also made `cause` an enumerable property in `AxiosError.from`, which a later fix
(#10913) made non-enumerable to avoid circular JSON. That is listed as a related valid finding,
not the answer.

How it was picked: mined with `reviewreplay mine` (language-aware miner, PR #16) while building
real-013, which comes from a different axios fix. The fix message names the commit and blame
agrees. Signals: message reference=True, blame agrees=True.

No third-party code was run; the evidence is the two diffs and the fix's message.
