You grade findings from a code review against an answer key. Be strict and literal.

Answer key — real bugs in this change (may be empty):
{bugs}

Answer key — spots that look suspicious but are correct (may be empty):
{known_ok}

Other real problems already known in this change (not answer-key bugs, but fair to report):
{related}

Findings from the review:
{findings}

For each finding (by index), decide:

1. `same_bug_as`: the id of the answer-key bug this finding describes, or null.
   - It must describe the **same defect**: the same wrong behavior, for the same cause. Pointing at the right
     lines with a different complaint does NOT count. A finding that names the right cause but phrases it
     differently DOES count.
   - Only choose among the bug ids listed in that finding's `candidates`. If `candidates` is empty, answer null.
2. `verdict`:
   - `matches_truth`: `same_bug_as` is set.
   - `valid_other`: not an answer-key bug, but the finding describes a real defect in the changed code that
     would cause incorrect behavior. Claims that contradict the "suspicious but correct" notes are NOT valid.
     Always `valid_other`: a finding that describes one of the "other real problems already known", and a
     finding that the change's tests fail to cover an answer-key bug.
   - `invalid`: the claimed problem is not real, is about unchanged code with no new effect, is pure style,
     or contradicts the answer key's notes.
   - `unsure`: you cannot tell from the information given.
3. `reason`: one short sentence.

Return one entry per finding index, in order.
