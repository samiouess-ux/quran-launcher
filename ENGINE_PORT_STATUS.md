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
- No successful Actions run or rendered MP4 has been verified yet.
- The old browser Canvas/WebM renderer remains in src/app.js and must be replaced/retired only after the new workflow path is tested.
- No Telegram credentials or secrets were copied.

## Next
1. Run the launcher workflow and verify its MP4 artifact.
2. Extend verified Quran text/translation coverage and audio support safely.
3. Connect launcher controls to a secure workflow trigger without placing GitHub tokens in browser code.
