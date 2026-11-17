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
