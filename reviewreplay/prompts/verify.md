You check one claim from a code review against the code itself. Be strict: a claim is settled only by
code you have read, never by what a library or function "usually" does.

The change under review: {title}

The claim:
{claim}

Your working folder holds:
- `project/`: the repository after the change
- `change.patch`: the change under review
- `libs/`: third-party source the claim may depend on. {libs}

Spots in this change known to look suspicious but to be correct:
{known_ok}

Other real problems already known in this change:
{related}

Use Read, Grep and Glob to find the code that decides the claim: the changed lines, the functions they
call, and any library code they rely on. Then answer:

- `confirmed`: the code shows the claimed defect happens in the changed code, for the reason given (or a
  reason close enough that a fix for one fixes the other). A known problem from the list above counts.
- `refuted`: the code shows it does not happen: a guard, a caller, a library behaviour or a test makes the
  claimed failure impossible, or the claim contradicts a "suspicious but correct" note.
- `unsure`: the deciding code isn't here (for example a library whose source is not in `libs/`), or what
  you read leaves both readings possible. Prefer `unsure` to a guess.

`evidence`: one to four exact quotes that decide it, each with its file path relative to your working
folder (`project/...`, `libs/...` or `change.patch`) and the line number. Copy each quote character for
character from the file, one to three lines long. Quotes are checked against the files; a verdict whose
quotes can't be found is treated as `unsure`.

`reason`: two or three sentences: what the code does, and why that confirms or refutes the claim.
