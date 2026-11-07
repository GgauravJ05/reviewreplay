Real bug from huggingface/accelerate (Apache-2.0). PR #3985 (92cc533, 2026-04-23) moved the
fp32 upcast before `fully_shard`, but `original_sd = model.state_dict()` was still captured
earlier, so with mixed precision and `cpu_ram_efficient_loading=True` rank 0 broadcasts bf16/fp16
tensors into fp32 buffers on other ranks and `dist.broadcast` hangs. Fixed in d1d2bba (#4021,
2026-04-27). Found by `reviewreplay mine` (message reference and blame agree); answer key drafted
by `init` and confirmed against the fix commit's message and diff. Not executed locally.
