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
