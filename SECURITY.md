# Security

ReviewReplay runs third-party AI reviewers on code. It is designed so that:

- reviewers run **read-only**, in a separate exported copy of the project with no git history;
- it never stores your API keys or tokens; they stay in your own environment;
- it sends code only to the reviewer you configure, under that provider's terms.

If you find a way around any of these, or another vulnerability, please report it privately through
[GitHub's private vulnerability reporting](https://github.com/GgauravJ05/reviewreplay/security/advisories/new)
rather than in a public issue. You'll get a reply within a few days.
