# Quran Launcher — Original Engine Port Status

## Safety boundary
- Destination repository: samiouess-ux/quran-launcher
- Working branch: feature/islamic-tiktok-engine-port
- Source repository: samiouess-ux/IslamicTikTokAutomation
- Source branch: feature/telegram-review-notifications
- The source repository and its branch are read-only for this port. No changes were made there.
- quran-launcher main was not changed.
- No TikTok publishing, Telegram bot credentials, or browser-side GitHub token.

## Verified renderer
- GitHub Actions run 44157628660 completed successfully.
- Original renderer safety tests, Quran validation, official audio preparation, rendering, MP4 verification, and artifact upload all succeeded.
- The render uses the approved Ash-Sharh 94:5–6 passage and exact approved Maher Al-Muaiqly Hafs audio.
- Output: MP4, H.264/AAC, 1080x1920, 30 fps, 9.51 seconds, moving video background, Arabic verse overlay and Saheeh International English translation.
- The 9.51-second sample is not evidence that the desired 30–40-second production duration has been reached.
- Renderer strips inherited source metadata and chapters.

## Launcher connection — current state
- Replaced the misleading browser Canvas/MediaRecorder generator with an honest mobile launcher for the real Python/FFmpeg workflow.
- The launcher shows only the currently validated configuration: Ash-Sharh 94:5–6, Maher Al-Muaiqly Hafs, and automatic rotation from the approved moving-background library.
- The Run button opens this repository's GitHub Actions workflow page. The user must authenticate to GitHub and press Run workflow there; the static GitHub Pages site cannot securely dispatch a workflow itself.
- No personal access token or secret is embedded in the public page.
- The generated MP4 remains a review-only Actions artifact; no automatic TikTok or Telegram delivery.

## Not yet supported
- Selecting arbitrary surahs/ayahs from the launcher.
- Choosing other reciters or selecting individual background clips from the launcher.
- One-tap workflow dispatch directly from GitHub Pages.
- Telegram delivery.
These require reviewed source/audio coverage and a secure authenticated backend or an explicitly approved alternate handoff. Do not simulate these options in the UI.

## Next safe integration step
Build and verify a secure, low-cost authenticated workflow trigger before promising one-tap generation from the launcher. Extend surah/reciter/background options only after each exact Quran text, translation, audio file, rights, and renderer manifest passes validation.


## Daily automation investigation — 2026-11-17
- Confirmed GitHub's documented restriction: `schedule`, `workflow_dispatch`, and `repository_dispatch` require the workflow file to exist on the repository default branch; scheduled workflows run only from that branch.
- The default branch is `main`. It remains untouched by this work, per the project safety boundary.
- Therefore adding a cron trigger to this feature branch would be misleading: it would not produce scheduled runs.
- The current launcher workflow hardcodes the single user-approved sample passage Ash-Sharh 94:5–6. Running it three times daily would repeat the same passage, contrary to the no-repeat requirement.
- `content_rotation.py` selects only manifests explicitly marked `rotation_approved: true`; the current sample manifest is not such a production rotation entry. The draft 94:1–8 manifest is explicitly unapproved for production audio.
- The approved moving-background catalog contains multiple user-approved candidates, but this does not solve the missing approved Quran passage pool or scheduler trigger.
- Safe decision: do not add a fake schedule, do not repeat the same clip, do not place a GitHub token in the public launcher, and do not modify `main` or the original `IslamicTikTokAutomation` repository.
- Remaining prerequisites for hands-off daily operation: an approved pool of distinct Quran passage manifests with verified Arabic + Saheeh International English + exact official audio, and an authorized scheduling trigger that does not violate the branch protection boundary. Telegram delivery remains separate and must be connected without changing the original bot/webhook.


## Renderer visual improvements — 2026-11-17
- Replaced the single-background loop in `build_background_reel` with a multi-clip moving-video reel. It downloads only enough eligible approved portrait clips to cover the audio duration, verifies actual media duration with ffprobe, and uses 0.55-second FFmpeg crossfades between clips.
- The reel fails closed if the approved video library cannot cover the complete output duration after transition overlap; it does not silently stretch a single clip.
- Added timed alpha fade-in/fade-out for Arabic and Saheeh International English verse overlays at scene boundaries. Overlay images are looped at 30 fps for their exact scene interval so the alpha fades are frame-based rather than a single still frame.
- These are code changes only; the GitHub Actions render/test result for commits `5870d8e` and `167f4af` must be checked before calling the effects verified.
- Existing limitations remain: only Ash-Sharh 94:5–6 has exact user-reviewed audio; its current sample is 9.51 seconds. Do not fabricate 30–40 second content or mark other visual templates approved without review.
- No scheduler/cron, Telegram, original engine repository, default branch, or GitHub Pages changes were made.

- Follow-up robustness fix: skipped/unavailable background candidates now advance the candidate cursor rather than risking a duplicate download when filling the crossfade reel.
- Latest renderer commit: `375216afd7a20aee342ea4357f0110e8a4571a02`. Runtime FFmpeg validation is still pending; no success is claimed until the Actions render completes and its output is inspected.

- Readability improvement: Arabic surah title, Arabic ayah text, ayah-number ornament, and Saheeh International English overlay now use a restrained dark stroke for legibility over bright moving footage. Original Quran strings and colors are unchanged.
- Renderer commit: `350fda0c9aaf9ce7e26974243828007bb9c9c9bc`.


## Passage duration alignment — 2026-11-17
- Corrected the official contiguous-ayah preparation defaults from a 60s target / 65s cap to a 35s target / 40s hard cap, matching the intended short-form production limit.
- Added regression tests for target/cap values, contiguous selection, no-over-cap behavior, preserving a single long ayah without trimming, and rejecting an ayah that alone exceeds 40s.
- Added the new test file to the isolated feature-branch Actions workflow.
- Commits: 2c562cf6ddf9373ced62b2f6203d1cd52aa749df (duration defaults), 9a150c75121848d7fc97bf20bc51dfeca011e64f (tests), bf83f151b4e82a7dc631ed7edc0ad220b45927f9 (workflow).
- Runtime validation is pending the Actions run triggered by the feature-branch push. The currently approved launcher sample remains 9.51s; this change does not invent extra approved verses or claim the current sample is 35s.

## Background rotation runtime verification — 2026-11-17
- Inspected the active root workflow `.github/workflows/quran-launcher-engine-render.yml`: its render command explicitly passes `--background-rotation` and a per-run key (`launcher-run-${GITHUB_RUN_ID}` when no manual key is supplied). Background rotation is therefore active in the current launcher render workflow, not merely present as unused code.
- Inspected successful run 44164005349, job 134325065874. The job completed all steps successfully, including safety tests, Quran validation, official audio preparation, render, MP4 checks and artifact upload.
- The runtime log confirms the selected moving-video background was `pexels-historic-mosque-stained-glass-30733250`; output was 9.51s. This proves the active workflow selected a catalog background, but this short sample needed only one clip; it does not yet demonstrate a multi-clip crossfade sequence.
- The catalog currently has 11 candidates passing the strict portrait 9:16 + user approval + download verification filter. Some other approved candidates are excluded because their stored aspect ratio/dimensions are landscape or incomplete; do not silently treat them as eligible portrait backgrounds.
- Confirmed limitation: the active root workflow still hardcodes `content/first_video.json` and the exact approved Ash-Sharh 94:5–6 audio. It does not yet use `content_rotation.py` or `select_review_manifest.py`. The separate workflow under `engine/.github/workflows/` is nested and is not a GitHub Actions workflow entry point; it must not be assumed active.
- No code behavior, launcher UI, default branch, Telegram integration, cron, or source repository was changed in this verification update.


## Rotation integration audit — 2026-11-17
- Re-read the active root workflow and confirmed it passes `--background-rotation`; the renderer imports `background_rotation.order_backgrounds` and consumes the catalog. The nested `engine/.github/workflows/render-manifest-video.yml` is not an active GitHub Actions entry point.
- Re-read `content_rotation.py`, `prepare_official_quran_passage.py`, and the manifest validator. The content rotation helper is not called by the active root workflow. The official audio passage preparer can probe contiguous exact audio to a 35s target / 40s cap, but it does not produce verified Arabic text or Saheeh International translations and cannot by itself create a renderable approved Quran manifest.
- Reconfirmed that only Ash-Sharh 94:5–6 has the exact user-reviewed audio approval. The 94:1–8 draft remains preview-only and is not a production rotation pool. Do not apply the 94:5–6 approval to any other passage.
- Corrected stale top-level metadata in `engine/data/background_candidates.json`: it now accurately states that the active renderer consumes the catalog and documents the strict 9:16 eligibility filter. This was a documentation-only correction; selection/render behavior was not changed.
- Safe next blocker: build a separate, fail-closed passage preparation pipeline that verifies exact Arabic and Saheeh International text against trusted catalogs, attaches only the matching official Hafs audio, and emits preview-only manifests until the exact recording is reviewed. The current hardcoded known-good 94:5–6 render remains unchanged.
- No launcher UI, default branch, original engine repository, Telegram bot/webhook, or scheduler was changed.


## Content rotation safety tests — 2026-11-17
- Added `engine/tests/test_content_rotation.py` to cover explicit `rotation_approved` gating, mandatory user-review/approval-required metadata, auto-publish rejection, recent-item exclusion, distinct batch selection, insufficient-pool fail-closed behavior, unsupported content types, and malformed manifest handling.
- Added this test suite to the active root GitHub Actions workflow. This validates the existing rotation helper but does not connect it to production rendering: the active workflow remains pinned to the known-good Ash-Sharh 94:5–6 manifest.
- No new Quran passage was approved, no audio approval was transferred, and no translation rights were presumed. The current manifest pool is intentionally not expanded until each exact Arabic/English/audio combination has been reviewed.
- Changes are isolated to `feature/islamic-tiktok-engine-port`; no UI, main branch, Telegram bot/webhook, scheduler, or source repository changes.
- Pending verification: GitHub Actions must run the newly added rotation tests successfully before this addition is considered validated.


## Content rotation hardening — 2026-11-17
- Corrected the earlier pending-verification note: workflow run 44183829571 (run 30, commit 24003a6c3c903ec147c29c939b82136824b89f62) completed successfully. Its full render, technical MP4 verification, and review-only artifact upload passed.
- Hardened `engine/src/content_rotation.py`: non-object JSON roots, unreadable/invalid JSON, malformed publishing metadata, missing approval metadata, and auto-publish values other than explicit false are treated as ineligible rather than causing an exception or weakening the gate.
- Batch size validation now explicitly rejects booleans (Python treats bool as int).
- Expanded `engine/tests/test_content_rotation.py` with malformed root/approval metadata and boolean batch-size regressions.
- Workflow run 44188036449 (run 31, commit 7c1ba87554cea464e6aa6ea8da4ed3506cc3eb4f) completed successfully. The full test step, Quran validation, official audio preparation, render, MP4 verification, and review-only artifact upload all passed.
- Workflow run 44188042971 (run 32, commit bfdc379a12f5c272fd6067f533d2f851a1ff5cf2) completed successfully. The expanded malformed-metadata tests, Quran validation, official audio preparation, render, MP4 verification, and review-only artifact upload all passed. Artifact ID: 14374488474 (expires 2026-11-24).
- These changes only harden the existing selector and its tests. They do not enable content rotation in the production renderer because there is still no pool of distinct user-reviewed Quran/audio manifests.
- The active renderer remains pinned to the unchanged Ash-Sharh 94:5–6 approved sample. No new recitation was marked approved, no translation reuse rights were presumed, and no new content was added to the production pool.
- No changes to the launcher UI, `main`, original IslamicTikTokAutomation repository, Telegram bot/webhook, cron, or TikTok publishing.


## Source-to-destination port audit — 2026-11-17
- Compared the recursive file trees of source branch `IslamicTikTokAutomation:feature/telegram-review-notifications` and destination branch `quran-launcher:feature/islamic-tiktok-engine-port`.
- Source contains 196 tracked files; destination contains 38 tracked files.
- 23 source files have byte-identical counterparts under `engine/`; 8 counterparts differ and require deliberate review rather than blind overwrite.
- 165 source files do not yet have counterparts. This includes 23 Python source modules, 35 test files, the existing Al-Ikhlas candidate manifest, 5 data/reference/history files, and all 36 tracked background-photo assets.
- Missing source modules include the original orchestration entry point, Quran batch rendering, daily content selection, requested-passage handling, dua renderer, cover/background review tooling, and Telegram request/delivery modules. These are not all to be activated: Telegram delivery/bot integration remains deferred and must not be copied into an active workflow without a separate safe integration.
- The current destination launcher is still a narrow GitHub Actions launcher, not a complete port of the original engine's capabilities.
- Correct next work is a dependency-aware port of the original engine modules and their tests, plus required reviewed local assets/manifests, into the destination feature branch. Preserve the current working renderer and UI; do not bulk-copy legacy workflows, secrets, generated output, or Telegram deployment wiring.
- This audit is read-only with respect to the source repository. No source files, source workflows, Telegram bot/webhook, destination main branch, Pages deployment, scheduler, or launcher UI were changed by this audit.


## Dependency-aware original engine port — 2026-11-17
- Continued the port from the read-only source branch `IslamicTikTokAutomation:feature/telegram-review-notifications` into `engine/` on `feature/islamic-tiktok-engine-port`.
- Added the original non-Telegram engine modules for Quran batch building/rendering, requested-passage range selection, daily content selection/orchestration, Tunisian day status, draft manifest generation, background review preparation, cover-template previews, dua rendering, and Quran reference validation.
- Added the original candidate manifest for Surah Al-Ikhlas 112:1–4 and the missing background review/history/reference metadata JSON/Markdown files. Existing destination copies of the Quran Uthmani reference, approved Ash-Sharh manifest, background candidates, and photo manifest were preserved rather than overwritten.
- Added regression tests for the newly ported modules (batch building, draft manifests, background review, renderers, selection, orchestration, reference validation, asset rotation, templates, captions, and Tunisian day status).
- Expanded the active feature-branch Actions workflow to run these ported regression tests before the existing approved Ash-Sharh render. Workflow change commit: `375d746a51a1dcf54fcb459fea5433d1a869722f`. The resulting Actions run must complete successfully before the newly ported modules are considered validated.
- Latest tree comparison: source has 196 tracked files; destination has 78. 71 source files now have destination counterparts. Remaining 125 source paths include six Telegram-specific modules, their associated tests, additional reference/catalog tests, 36 photo/ZIP binary assets, and other files not yet ported.
- Deliberately not copied or activated: Telegram bot/request/delivery modules and deployment workflows. No bot token, webhook, or external scheduler was touched. Binary photo/ZIP assets cannot be safely recreated through the available text-file GitHub write operation; they need a verified binary transfer path rather than corrupt text encoding.
- This is a partial, dependency-aware port, not yet a complete port. No claim is made that the app now exposes all original engine features. The launcher UI, `main`, GitHub Pages configuration, original source repository, and production delivery/scheduling behavior remain unchanged.


## Additional original catalog and reference test port — 2026-11-17
- Added original regression suites for translation catalog generation, Uthmani catalog generation, Quran video catalog generation, Quran audio part handling, audio batch preparation, repository-rotation safety, background reel construction, background additions review, Al-Ikhlas reference validation, and Quran text validation.
- Added all of these suites to the feature-branch Actions test step. Latest workflow update commit: `fb5aed40ea3ab529a2777ea5706a84f325cceb9e`.
- GitHub Actions run `44190756265` was observed in progress on an earlier test-file commit; it is not the final validation for the expanded test list. The workflow run for commit `fb5aed40ea3ab529a2777ea5706a84f325cceb9e` remains the required validation target.
- The original source's non-Telegram `src/` modules now all have destination counterparts. Six Telegram-only modules remain deliberately excluded pending a separate safe integration.


## Continued port and background-reel regression repair — 2026-11-18
- Added the standalone Quran request parser dependency and its regression test under `engine/src/` and `engine/tests/`. This parser is not wired to Telegram delivery; the original bot, webhook, and credentials remain untouched.
- Updated the feature-branch workflow to execute the parser regression test.
- Transferred 34 of the 36 source background-photo/cover-archive binary assets into `engine/assets/background_photos/` using Git's base64 blob API, preserving binary data. Two source JPEGs (`pexels-28975736.jpg` and `pexels-37099396.jpg`) returned empty content from the source file endpoint and were deliberately not committed as empty/corrupt files; they remain outstanding for a different binary retrieval method.
- Fixed the destination renderer's short-clip background logic so a single approved moving clip can loop to cover the narration duration rather than forcing an extra scene. Kept the final-duration verification in place and aligned the test's expected selected-ID list with the renderer's existing return contract.
- The first expanded test run exposed the short-clip regression; a follow-up run then showed the initial selection loop still fetched a second clip. That was corrected in commit `59e7e90e6e59690a024c210cc0fe1679ed7cf111`.
- Latest observed Actions run: `44250015150` on commit `59e7e90e6e59690a024c210cc0fe1679ed7cf111`, in progress at the time of this update. Do not consider the renderer regression or overall port validated until this run completes successfully.
- No UI, `main`, source repository, Telegram integration, scheduler, TikTok publishing, Pages settings, or approved Ash-Sharh sample was changed.


## Background short-clip loop regression fix — 2026-11-18
- Inspected failed Actions run `44250015150` and its complete job log. All preceding regression suites passed; `test_loops_one_short_clip_to_cover_full_audio` failed because the builder fetched a second candidate even though the intended behavior was to loop the first short approved clip, exhausting the test's duration-probe mock before final-output verification.
- Fixed `engine/src/render_video_scenes.py` so the coverage-fill loop is skipped when exactly one prepared clip is shorter than the target and is therefore intended to loop. The final ffprobe duration check remains active; multi-clip reels still use the existing crossfade coverage logic.
- Fix commit: `7396a178dcc84410d21cd8146f7bc3168f62ba08` on `feature/islamic-tiktok-engine-port`.
- The existing regression test already asserts that only `clip-a` is selected, output duration is the full 10 seconds, FFmpeg loops the source, and only one render is performed. GitHub Actions validation for the fix is pending; do not call this fix verified until the new run completes.
- No launcher UI, `main`, source `IslamicTikTokAutomation` repository, Telegram integration, scheduler, Pages settings, or TikTok publishing was changed.


## Renderer regression fix verified — 2026-11-18
- GitHub Actions run 44252972286 completed successfully on commit 7396a178dcc84410d21cd8146f7bc3168f62ba08.
- All renderer safety regression suites passed, including the short-background-clip loop regression that failed in the preceding run.
- Quran manifest validation, checksum-pinned official Hafs archive inventory, exact approved Maher Al-Muaiqly audio preparation, moving-background render, MP4 technical verification, and review-only artifact upload all completed successfully.
- Render log confirms the selected moving-video background was `pexels-islamic-dome-geometric-40564360`. Output passed as H.264/AAC, 1080x1920, 30 FPS, with Quran audio, duration 9.51 seconds.
- Review-only artifact: `quran-launcher-original-engine-review`, artifact ID `14405510851`, expires 2026-11-25. Run URL: https://github.com/samiouess-ux/quran-launcher/actions/runs/44252972286
- This verifies the isolated renderer workflow and regression fix only. The launcher remains a limited sample launcher; full interactive surah/ayah/reciter/background controls and the complete original-engine integration are not yet finished. The approved sample remains 9.51s, not the intended 30–40s range.
- No source repository, `main`, launcher UI, Telegram bot/webhook, scheduler, Pages settings, or TikTok publishing was changed.


## Opening cover preview regression test — 2026-11-18
- Ported the source repository's `test_opening_cover_previews.py` into the isolated launcher engine test suite.
- Made the test self-contained by creating a temporary reference image and patching the preview module's reference-image path; the test no longer depends on an untracked local image file.
- Added the test to the active root GitHub Actions workflow.
- Workflow run 44255158636 (run 106, commit 44fbefe02a0aac63cc3aa362f43a16c6391c7a9d) completed successfully. All renderer regression tests, Quran/manifest validation, official audio preparation, moving-background render, MP4 technical checks, and artifact upload passed.
- The cover preview test verifies four distinct 1080x1920 templates and rejects empty titles or invalid ayah ranges. These are preview-only templates and are not yet connected to production video rendering or launcher controls.
- The launcher remains a manual GitHub Actions handoff; the sample passage remains Ash-Sharh 94:5–6 at 9.51 seconds. No new surah/audio was approved.
- Scope unchanged: no edits to `main`, the source IslamicTikTokAutomation repository, Telegram bot, scheduler, GitHub Pages settings, or TikTok publishing.


## Content rotation approval gate hardening — 2026-11-18
- Tightened `engine/src/content_rotation.py`: a manifest is eligible only when `content_type`, `rotation_approved`, `publishing.approval_required`, and `publishing.auto_publish` are all explicitly present with the required values.
- Removed the permissive default that treated a missing `content_type` as Quran and a missing `auto_publish` flag as safe. Missing metadata now fails closed and cannot enter the review rotation.
- Added regression tests for absent content type and absent auto-publish metadata.
- Commits: `6e93a0e0d51394096ac6461999b5cf5d0ac13ede`, `83b5d044a5af398a0152467d89081e3466e398da`, `ad5280bbfb137fe0e8aa942a0957db4325ab6acc`.
- GitHub Actions verification is pending. The fixed Ash-Sharh sample workflow remains unchanged; this hardening does not enable unreviewed Quran content or change the UI.
- Scope unchanged: no edits to `main`, source IslamicTikTokAutomation, Telegram, scheduler, Pages settings, or TikTok publishing.


## Shared content-manifest validator hardening — 2026-11-18
- Tightened `engine/src/validate_content_manifest.py` so `content_type`, `audio.kind`, and `publishing.auto_publish=false` must be explicitly declared. Missing metadata is no longer silently inferred as Quran, recitation, or safe no-auto-publish.
- Updated the existing approved Ash-Sharh sample to explicitly declare `content_type=quran` and `audio.kind=quran_recitation`; its reviewed passage and rendering settings were not changed.
- Added regression tests for missing content type, audio kind, and auto-publish setting.
- Commits: `7faa39702dd20ccaabd0ae2d90437086afcecb1b`, `cb08e90f8c9e29bb0f861788b389cb5b72b01bac`, `658f449941e9d87105e37eae6b30ce8b3aaaa33e`.
- GitHub Actions validation is pending. No new surah or reciter was enabled, and the launcher UI remains unchanged.
- Scope unchanged: no edits to `main`, source IslamicTikTokAutomation, Telegram, scheduler, Pages settings, or TikTok publishing.


## Draft manifest metadata consistency — 2026-11-18
- Audited all JSON manifests under `engine/content/`. The Ash-Sharh 94:1–8 draft lacked an explicit content type and rotation state, so it now declares `content_type=quran` and `rotation_approved=false`.
- This is metadata consistency only; the draft remains ineligible for rotation and production because it exceeds the 40-second cap and still has unresolved review gates.
- Commit: `c2ad5b109db41dba64272e8ce6b22722dbde8cac`.
- Current content pool audit: one approved first-test passage, one unapproved candidate (Al-Ikhlas), and one unapproved Ash-Sharh draft. There is not yet a pool of three distinct production-approved passages for the daily batch.
- Scope unchanged: no edits to `main`, source IslamicTikTokAutomation, Telegram, scheduler, Pages settings, or TikTok publishing.


## Quran review-preview duration cap aligned — 2026-11-18
- Found a mismatch: the review-batch audio preparation stage allowed up to 45 seconds, while the renderer and the user's approved limit are 40 seconds maximum.
- Aligned the audio preparation cap, deferred-status labels, report metadata, and regression-test expectations to a strict 40-second maximum. Complete ayahs remain intact; no ayah is truncated and short passages are not padded to an artificial minimum.
- No production content was approved or enabled by this change. The single approved sample workflow remains separate.
- Validation will be reported only after the queued GitHub Actions run completes.


## Canonical Quran catalog join validation — 2026-11-18
- Hardened `build_quran_video_catalog.py` so the join validates every key as a numeric `surah:ayah` reference, rejects malformed/out-of-range surah references, and—when joining the full 6,236-ayah corpus—requires the exact canonical 114-surah verse-reference set.
- This closes a gap where three equally sized catalogs could previously join successfully even if they shared invalid or non-canonical verse keys.
- Added regression coverage for malformed keys and out-of-range surah numbers. The existing human-review, translation-rights, exact-audio approval, and rendering-disabled gates remain unchanged.
- Pending GitHub Actions validation; no Quran text, translation, audio, content approvals, UI, default branch, source repository, Telegram, scheduler, or publishing behavior changed.


## Canonical-reference regression assertion correction — 2026-11-18
- Actions run 44260228601 exposed a test-only assertion mismatch: the validator correctly rejected `115:1`, but its more specific error wording did not match the test's generic expected phrase.
- Updated the out-of-range-surah error to consistently identify the input as an invalid Quran verse key. Validation behavior is unchanged.
- The canonical surah verse-count table was independently checked: 114 entries totaling exactly 6,236 ayahs.
- Re-run the complete feature-branch workflow before treating this correction as verified.


## Canonical Quran catalog validation verified — 2026-11-18
- Feature-branch Actions run 44260400866 (run 121) completed successfully on exact commit eaa3e4d5741dd819381b2fcc9b00217c17cc17d0.
- The full renderer safety regression suite passed, including canonical Quran reference validation; approved Ash-Sharh manifest validation; checksum-pinned official Hafs inventory; exact approved Maher Al-Muaiqly audio preparation; moving-background MP4 render; technical MP4 checks; and review-only artifact upload.
- Review artifact: `quran-launcher-original-engine-review`, artifact ID 14408270322. This is a review artifact from the unchanged Ash-Sharh 94:5–6 sample, not a new approved passage.
- The joined 6,236-ayah catalog and review-batch candidate pipeline are still preparation-only; human text, translation-rights, exact-recording, and background approval gates remain closed. The active launcher workflow still renders only the approved Ash-Sharh sample.
- No UI, `main`, source repository, Telegram bot/webhook, scheduler, Pages settings, or TikTok publishing was changed.


## Review-batch delivery-history reference validation — 2026-11-18
- Hardened the review-candidate builder to reject malformed Quran verse keys in its joined-catalog input and malformed or unknown verse references in delivery history.
- This prevents corrupt/stale history entries from being silently ignored and causing a previously delivered ayah to be selected again.
- Added regression tests for malformed history references, references missing from the joined catalog, and malformed catalog keys. Existing review-only, no-render, no-Telegram, and no-auto-publish boundaries are unchanged.
- Pending feature-branch Actions validation; no content was approved and the active renderer remains pinned to Ash-Sharh 94:5–6.


## Review-batch catalog key validation ordering — 2026-11-18
- Corrected validation order in the review-batch builder: it now validates each catalog key before parsing or sorting surah numbers. Previously a non-string or malformed key could raise an incidental Python parsing error before the intended fail-closed validation message.
- Expanded regression coverage for malformed strings, out-of-range surah numbers, zero ayah numbers, and non-string keys.
- This is defensive input validation only; review-only status and all approval gates remain unchanged. Feature-branch Actions validation is pending.


## Bounded review-audio preparation — 2026-11-18
- Optimized `prepare_quran_review_batch_audio.py` to inspect contiguous whole ayahs sequentially only until the first ayah that takes the passage over the 40-second cap. It no longer downloads and trims the rest of a long surah suffix when those later ayahs cannot be part of the current video.
- The first non-fitting ayah is still inspected to establish the exact continuation boundary; selected audio remains a contiguous prefix, with no ayah truncation. Remaining ayahs stay queued for a future candidate batch.
- Expanded the duration-boundary regression test with a fourth ayah that deliberately has no inventory mapping: successful preparation proves the code stops after inspecting the first overflow ayah and does not fetch later material.
- This is a preparation-efficiency change only. Candidate approval, rendering, Telegram delivery, and auto-publishing remain disabled.
- GitHub Actions validation is required before considering this optimization verified.

- Follow-up defensive correction: the overlong-single-ayah status now uses the measured duration of the first inspected ayah rather than comparing inspected and full candidate list lengths, which differ after bounded inspection.

- Regression-test expectation corrected to match the report contract: the overflow ayah is downloaded/probed only to establish the boundary, but only selected ayahs are exposed in the prepared-audio report. The test now checks the overflow source exists, no later source is fetched, and overflow audio is not included in the output mapping.


## Partial-surah continuation selection fix — 2026-11-18
- Found a production-mode selection gap: the review-batch builder received `used_surahs` and therefore skipped all partially delivered surahs, even when delivery history showed an undelivered contiguous suffix. Existing continuation tests did not exercise the production argument combination.
- Changed candidate selection to prioritize a valid unused suffix from a partially delivered surah before choosing fresh surahs. Fully delivered surahs remain excluded; used ayahs and gaps are still skipped.
- Added production-mode regression coverage for continuation priority and fully completed surah exclusion. The workflow remains review-only; no rendering, delivery, approval, or publishing is enabled by this change.
- This fix is not considered validated until the feature-branch GitHub Actions run passes.


## Production continuation gap regression — 2026-11-18
- Added a production-argument regression test for a partially delivered surah whose delivery history contains a later used ayah after an earlier gap.
- The expected selection begins after the latest delivered ayah, preserving all previously delivered references and choosing only the remaining contiguous suffix.
- Test commit: `a0ae6d837eb57a42ea4bc26526360305ea65bc5e`.
- This is test coverage only; no selection behavior or content approval changed. GitHub Actions validation is pending.
- Current Actions run 44271812150 is still in progress at the FFmpeg/Arabic-font installation step; the latest branch run that included the continuation fix was cancelled before tests. Do not treat the new test or continuation fix as validated until a run on the current branch head passes.
- Scope remains unchanged: no UI changes, no `main`, no source-repository writes, no Telegram delivery, no scheduler, and no TikTok publishing.


## Partial-pool selection hardening — 2026-11-18
- Found two additional edge cases while reviewing production-mode continuation: the builder rejected a batch before considering a remaining partial surah when no fresh surahs remained, and an explicit `only_surahs` request could be bypassed by a partial surah outside that requested set.
- Selection now counts eligible partial continuations together with fresh surahs before validating batch size. It selects only the required number of fresh surahs after prioritizing partial continuations.
- An explicit `only_surahs` restriction is now also applied to partial-continuation candidates, preserving Friday-only Al-Kahf behavior.
- Added regression tests for a single remaining partial surah after the fresh pool is exhausted, and for enforcing an explicit surah-only request.
- Source commit: `97ca0c1`; tests commit: `4fb69c6`.
- Pending GitHub Actions validation on the latest branch head. Rendering, audio approval, Telegram delivery, and auto-publishing remain disabled for candidate batches.
- Workflow dependency-install step was also bounded: it checks runner-provided FFmpeg/Amiri first and uses capped apt retries/timeouts only when installation is needed. Workflow commit: `97c132b`.
- No launcher UI, `main`, original source repository, Telegram bot/webhook, scheduler, Pages settings, or TikTok publishing was changed.


## Explicit-surah partial continuation and CI queue fix — 2026-11-18
- Follow-up review caught that the previous hard-boundary fix excluded an already-used surah from the partial continuation pool when `only_surahs` was supplied. The selection now validates `used_surahs` in both modes, excludes fully used surahs from fresh selection, and still allows the requested surah's unused contiguous suffix.
- Regression test now requests only surah 2 while marking surah 2 as partially delivered, and expects continuation at ayah 3. This is the strict case needed for a Friday Al-Kahf-only batch.
- Commits: `3987ddd` (selection), `f39da25` (regression test).
- CI concurrency now cancels an older in-progress run when a newer commit needs validation. This addresses the stale run that remained marked in progress at the FFmpeg/font installation step and blocked newer queued runs. Workflow commit: `112ab23`.
- Latest validation remains pending; do not treat any of these new tests as passed until the latest-head run completes successfully.


## Al-Fatihah complete render and moving-background rotation validation — 2026-11-18
- Feature-branch workflow run `44292617353` completed successfully on commit `ac0d3617e1ad02dfe96e319f37adaa8c86240e25`.
- Complete Al-Fatihah 1:1–7 was rendered as one review-only video; no splitting, speed changes, or removal of recitation. Output: 51.95 seconds, 1080x1920, 30 FPS, with Quran audio.
- The workflow reused the original engine's `trim_edge_silence` helper for each ayah. It removed only detected leading/trailing silence, retained 0.12 seconds at each edge, and did not trim inside the recitation. Added inter-ayah silence is 0.0 seconds. The seven per-ayah reports recorded approximately 1.899–2.526 seconds of edge silence removed per file.
- The moving-background renderer selected four distinct approved video clips and joined them with 0.55-second crossfades: `pexels-mountain-lake-37675265`, `pexels-waterfall-forest-12110531`, `pexels-mosque-river-mostar-27529804`, and `pexels-mosque-waterfront-12536108`. It no longer repeats the first short clip across the entire narration when other approved clips are available.
- Visual inspection of extracted frames across the complete video confirmed the four backgrounds and the Arabic/English verse overlays remain present in sequence. The fourth background naturally occupies the final longer section; no missing overlay interval was observed in the sampled timeline.
- Review artifact: `quran-launcher-original-engine-review`, artifact ID `14422146662`, expires 2026-11-25. URL: https://github.com/samiouess-ux/quran-launcher/actions/runs/44292617353/artifacts/14422146662
- This remains a review-only test. Al-Fatihah is not approved for production, and no photos were activated. The 33-image photo gallery still requires the user's individual approval. No UI, Pages settings, Telegram, scheduler, TikTok publishing, `main`, or original source repository was changed.


## Keep Quran verse frame steady between ayahs — 2026-11-18
- Commit: `724e3cee48c2d2dd614d6a11002c92871fcfc9f8` on `feature/islamic-tiktok-engine-port`.
- Removed the per-ayah fade-in/fade-out from the Arabic overlay layer. This prevents the shared decorative frame from fading out and back in at every ayah boundary, which was perceived as a small flicker.
- Preserved the existing soft fade behavior for the English translation overlay and did not change background/photo/video transitions.
- The feature-branch review render workflow is running as #162 / run `44295292022`; initial regression tests, Quran text/manifest validation, and audio inventory preparation passed. Final MP4 verification and visual review are pending. Do not mark this change visually validated until the run completes and the resulting video is inspected.
- Review-only; no production activation, UI/Pages, Telegram, scheduler, TikTok publishing, `main`, or original source repository changes.


## Temporary review artifact storage policy — 2026-11-18
- Reduced GitHub Actions artifact retention for both the cinematic Quran MP4 review workflow and the background-photo review gallery from 7/14 days to 3 days.
- Generated MP4s and review galleries remain Actions artifacts only; they are not committed into the Git repository. Source code, manifests, and approved assets remain in the repository as before.
- This retention setting applies to artifacts created by future workflow runs after this change. Existing artifacts keep their original expiry dates unless manually deleted.
- This does not change repository Git history or automatically delete existing committed files. No repository-wide retention setting, default branch, source repository, Pages, Telegram, scheduler, or publishing behavior was changed.
- Validation is pending the next feature-branch workflow runs; no claim is made yet that the new retention setting has been exercised by a fresh artifact.


## Al-Fatihah render and 3-day artifact retention verified — 2026-11-18
- Feature-branch workflow run `44296263880` completed successfully on commit `9f4eb7cf805c41e7471c1c1e2efb3b57b3d716ae`.
- All steps passed: renderer safety regression tests, Quran text/manifest validation, checksum-pinned official Hafs archive inventory, complete review-only Al-Fatihah recitation preparation, cinematic MP4 rendering, technical MP4 verification, and artifact upload.
- Review artifact: `quran-launcher-original-engine-review`, artifact ID `14424505862`, size 52,844,269 bytes. GitHub reports creation at 2026-11-18 11:39:38 UTC and expiry at 2026-11-21 11:39:36 UTC, confirming the new approximately 3-day retention policy for this fresh artifact.
- This confirms a technically valid MP4 was rendered and uploaded and that new artifact expiry is 3 days. It does not by itself constitute visual inspection of the frame across every ayah; do not claim the frame-flicker issue is visually resolved until the output is inspected.
- Review-only. No production activation, UI/Pages, Telegram, scheduler, TikTok publishing, `main`, or original source repository was changed.


- Follow-up visual inspection of the downloaded review MP4: extracted representative frames at 2-second through 51-second checkpoints. The decorative ayah panel/frame stayed in the same screen position and no obvious fade-out/fade-in flicker was visible in these sampled frames across ayah changes. Moving backgrounds changed through the sequence, and Arabic/English overlays remained visible in the sampled timeline. This is a sampled visual check, not a frame-by-frame proof.
- The inspected MP4 metadata reports H.264 video, AAC audio, 1080x1920, 30 fps, and 51.946 seconds duration. The complete Al-Fatihah output is therefore longer than 40 seconds; this matches the explicit full-surah/no-splitting decision for this review test and must not be treated as a global duration cap.

## Detailed ayah-boundary visual review — 2026-11-18
- Downloaded and inspected the exact MP4 from artifact 14424505862 (run 44296263880); no video or generated media was added to Git.
- Used the processed per-ayah audio durations in the workflow log to locate the six ayah boundaries at approximately 6.45s, 13.27s, 18.29s, 23.75s, 30.51s, and 36.89s.
- Extracted five frames around each boundary (approximately -0.10s, -0.033s, boundary, +0.033s, +0.10s) and reviewed the resulting contact sheet. The decorative panel/frame remains in the same layout and position; no obvious frame fade, jump, shake, or flicker is visible at the six sampled transitions. The Arabic ayah changes at the expected boundary; the English translation retains its intended soft transition. Background clips continue to change independently.
- This is a focused visual sample around all six ayah boundaries, not a pixel-by-pixel or full 30-fps audit. Record the result as “no obvious flicker in sampled boundary frames,” not as a mathematical guarantee of zero flicker.
- No renderer code change was needed based on this review. Keep the Arabic overlay fully opaque at scene boundaries; do not add fade-out/fade-in to the shared frame layer. Background and English translation fades remain separate.
- Review-only. No production activation, UI/Pages, Telegram, scheduler, TikTok publishing, main, or original source repository was changed.


## Quran Launcher UI alignment and isolated Al-Ikhlas audio review path — 2026-11-18
- Work continued only on feature/islamic-tiktok-engine-port; no changes were made to main or the original IslamicTikTokAutomation repository.
- Updated index.html so the launcher describes the actual verified review render (complete Al-Fatihah 1–7) instead of the obsolete Ash-Sharh 94:5–6 demo. The UI continues to link to the existing Al-Fatihah review workflow and explicitly states that output is review-only, with no Telegram delivery or TikTok auto-publishing. UI commit: e54bd1719b9eecd7fc717b899f7fdf97081f129a.
- Added engine/src/prepare_al_ikhlas_audio_review.py, which extracts the four complete Al-Ikhlas 112:1–4 MP3 members from the pinned official Maher Al-Muaiqly Hafs archive, checks each extracted member through the ZIP CRC path and FFprobe duration, calculates per-ayah SHA-256 values, and concatenates the original MP3 frames in order without speed changes, verse cuts, or added inter-ayah silence. It writes a report that explicitly leaves audio approval, rendering permission, Telegram sending, and TikTok publishing false. Script commit: 836912eb6d2baf3aa29fd71c646cb3dec860141b.
- Added isolated unit tests for complete four-ayah extraction, correct reciter/riwaya guard, and missing-ayah guard. Test file was corrected in follow-up commit 807550b1048d6533a7cb19549c121b5dbd4f43e5. These tests have not yet been confirmed as executed by GitHub Actions.
- Added root-level workflow .github/workflows/al-ikhlas-audio-review.yml. It validates the candidate is Al-Ikhlas 112:1–4, Maher Al-Muaiqly/Hafs, not rotation-approved, and not auto-published; runs the isolated tests; builds the official audio inventory from the pinned metadata/checksum; extracts the review-only audio package; and uploads a 3-day artifact. Workflow commit: 53f199a6c252ad9c8b6ccd4d84f7b41c6c1cce76.
- Updated the Al-Ikhlas candidate manifest to replace the rejected Islam Sobhi source with the official Maher Al-Muaiqly Hafs archive mapping. It remains candidate_not_approved_for_rotation, rotation_approved=false, audio.approved=false, and exact_recording_user_reviewed=false. Recording-specific redistribution rights are explicitly still pending independent verification (rights_verified=false); archive identity/checksum does not itself establish those rights. Candidate update commit: c095397d0e992c4e865de002a0d1bdd52797caa2.
- Verification limitation: the GitHub connector available in this session exposes workflow run/job/artifact reads but no workflow-dispatch action or general workflow-run listing action. The commit-workflow-runs wrapper only returns pull-request-triggered runs, and the combined commit status returned no statuses for the new workflow commit. Therefore no successful Actions run, extracted MP3, or review artifact is claimed yet.
- No changes to background catalogs or approvals, Telegram bot, scheduler, TikTok publishing, production activation, main, or the original source repository.
