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
