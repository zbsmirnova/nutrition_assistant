# Backend date resolution QA report

Date: 2026-09-23  
Scope: backend-owned effective-date resolution and resolver-version fencing  
Base: `23691a12c1b81ff7af6a96d4dfb5d34d9fb55054`  
Reviewed source ID: `c4754e6cd74f0783376982fc5244647e98642f0de793bfb7de6f89f77c156482`

Independent QA ran three focused probes: an undated source always uses the captured source-local date even when the model supplies a hint; supported, missing, invalid and conflicting date evidence stays within the documented resolution rules; and the changed semantics have a new frozen resolver identity. All three passed. The focused interpretation suite (14 tests) and Nebius protocol suite (18 tests) also passed.

Developer verification passed 87 offline tests, 59 PostgreSQL integration tests and 32 retained QA checks. The database runs used approved local access. No live provider call or user data was used by this slice.

The previous review correctly found that changing date semantics without changing `RESOLVER_VERSION` would let old unfinished contexts pass the worker's version guard. The implementation now advances `single-food-resolver-v3` to `single-food-resolver-v4`; prepared or applied commands remain recoverable without reparsing. No remaining defect was found in the reviewed source. The final evidence package adds documentation and retained logs after the runtime review; `reviewed_runtime_source_id` in the manifest preserves the exact source independently assessed.

Evidence:

- [independent-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/independent-output.txt?type=file&root=%252F)
- [resolver-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/resolver-output.txt?type=file&root=%252F)
- [nebius-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/nebius-output.txt?type=file&root=%252F)
- [offline-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/offline-output.txt?type=file&root=%252F)
- [integration-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/integration-output.txt?type=file&root=%252F)
- [retained-qa-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/retained-qa-output.txt?type=file&root=%252F)
- [source.patch](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/source.patch?type=file&root=%252F)
- [review-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/review-manifest.json?type=file&root=%252F)
- [independent-review-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-backend-date-resolution/independent-review-manifest.json?type=file&root=%252F)
