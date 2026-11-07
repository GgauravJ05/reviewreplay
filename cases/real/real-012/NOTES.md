# real-012 (peft-0b2c727f)

Introduced in `0f9bdad7fa609317ca4e2ce80c04a7fffc417299`: ENH Support Conv3d layer in LoRA and IA3 (#2082)
Fixed in `0b2c727f77df4eca39f9fc102fc389d1a92e2f92`: FIX Preserve Conv LoRA dilation and padding_mode (#3758)

Why this is a bug (drafted by claude-sonnet-5-5):
Commit A's LoRA conv layers build lora_A without the base conv's dilation and padding_mode, causing shape mismatches and wrong boundary behavior. Commit B fixes this.

Reviewed by hand against the upstream fix `0b2c727f77df4eca39f9fc102fc389d1a92e2f92` (https://github.com/huggingface/peft/issues/3697). Signals: message reference=False, blame agrees=False. No third-party code was run; the evidence is the fix commit, its tests and the linked issue.

Note: the Conv2d branch before this commit already omitted dilation/padding_mode; this commit rewrote the line for all conv types (adding Conv3d), so the bug is in the changed lines a reviewer sees, but it was carried over rather than first introduced here.
