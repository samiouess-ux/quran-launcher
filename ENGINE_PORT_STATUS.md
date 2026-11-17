# Quran Launcher — Original Engine Port Status

## Safety boundary
- Destination repository: samiouess-ux/quran-launcher
- Working branch: feature/islamic-tiktok-engine-port
- Source repository: samiouess-ux/IslamicTikTokAutomation
- Source branch: feature/telegram-review-notifications
- Source snapshot commit: a5c65d5330e3cb579629a71d5dedae185ab3efe3
- The source repository and its branch were read only. No changes were made there.
- quran-launcher main was not changed.

## Ported engine
- Original Python/FFmpeg renderers, scene renderer, background rotation and supporting helpers are under engine/src/.
- Original background video/photo catalogues and reviewed Quran reference data are under engine/data/.
- Approved test passage and exact Arabic validator are under engine/content/ and engine/src/.
- Selected original regression tests are under engine/tests/.
- A launcher-specific root workflow is available at .github/workflows/quran-launcher-engine-render.yml.

## Render workflow currently enabled
- Manual GitHub Actions workflow only; it does not publish to TikTok and does not send Telegram.
- Initial render is deliberately limited to the exact previously approved Maher Al-Muaiqly Hafs recitation for Surah Ash-Sharh 94:5–6.
- Uses the original scene renderer, rotating approved moving-video background candidates, Amiri Bold, and English translation overlay.
- Enforces MP4 1080x1920, 30 fps and a hard 40-second maximum.
- The renderer must pass exact Arabic reference validation before rendering.
- Workflow produces a review-only downloadable artifact.

## Not yet complete
- The browser launcher UI is still not connected to this workflow.
- Arbitrary surah/ayah selection and additional reciters are not enabled in the production render path. The existing reviewed Quran reference snapshot only covers limited passages, and the approved audio record in this port is the exact Ash-Sharh 94:5–6 sample. Do not bypass those validation/rights gates.
- Original renderer safety regression tests passed on GitHub Actions run 44156724565.
- Exact Quran Arabic validation and manifest safety checks passed on that run.
- Audio preparation then exposed a ZIP filename-encoding mismatch: metadata paths are UTF-8 while the downloaded archive directory names decode differently. The workflow now locates the exact verified verse members by their unique `10-094005-A08.mp3` / `10-094006-A08.mp3` suffixes after the full archive SHA-256 is verified. This correction is committed as 5c7c979861b5f2595bfaea75653f5fd93ad4a3bf; it still needs a fresh Actions run.
- A real review MP4 was rendered successfully in Actions run 44157053271: 1080×1920, 30 fps, H.264/AAC, 9.51 seconds, with the approved Maher Al-Muaiqly Hafs recitation and moving Pexels background `pexels-mosque-river-mostar-27529804`.
- The MP4 was downloaded and inspected: Arabic surah title/ayah overlay and Saheeh International English translation are visible. The sample is 9.51 seconds because the only exact user-approved test recording is Ash-Sharh 94:5–6; the 30–40-second production duration target still requires additional reviewed passages/audio.
- Inspection found source-location metadata inherited from the background clip. The scene renderer now strips source metadata and chapters from the final MP4.
- The official archive host intermittently returns 404/503; the pinned mirror is used with the full archive SHA-256 check when needed. A checksum-verifying Actions cache is now configured to avoid repeated 760 MB downloads.
- The old browser Canvas/WebM renderer remains in src/app.js and must be replaced/retired only after the new workflow path is tested.
- No Telegram credentials or secrets were copied.

## Operational note
- The official archive endpoint returned HTTP 404 in the latest test, and the checksum-pinned mirror did not support byte ranges. The original inventory builder safely downloaded the full 760,867,237-byte archive and verified its published SHA-256 before use. This makes the first render slower; archive caching can be added after the first successful render.

## Next
1. Re-run after metadata stripping/cache changes and verify the final artifact has no inherited GPS metadata.
2. Extend verified Quran text/translation coverage and audio support safely.
3. Connect launcher controls to a secure workflow trigger without placing GitHub tokens in browser code.
