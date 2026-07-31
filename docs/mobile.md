# Mobile app (Capacitor)

The React frontend (`app/frontend/react_app`) is wrapped with
[Capacitor](https://capacitorjs.com) rather than rebuilt as a separate native
app. Capacitor loads the same Vite build (`dist/`) inside a native WebView, so
every screen, Tailwind style, and library (`react-router-dom`, `recharts`,
`jspdf`) works unchanged on iOS and Android. There is no separate mobile
codebase to maintain.

## What's already set up

- `@capacitor/core`, `@capacitor/android`, `@capacitor/ios` pinned to
  **6.2.1** (dependencies), `@capacitor/cli` pinned to 6.2.1 (devDependency).
  Capacitor 7/8 require Node ≥20/≥22; if your machine is on an older Node,
  stay on 6.x until you upgrade, then `npm install @capacitor/core@latest
  @capacitor/android@latest @capacitor/ios@latest @capacitor/cli@latest`.
- `capacitor.config.ts` — `appId: com.triageai.esicarerouting`,
  `appName: TriageAI`, `webDir: dist`.
- `android/` — full native Android Studio project, scaffolded and synced.
- `ios/` — native Xcode project scaffolded, but **`pod install` has not run**
  (this dev machine has no CocoaPods and no full Xcode, only the Command Line
  Tools). Run this once on a Mac with Xcode + CocoaPods installed:

  ```bash
  cd app/frontend/react_app
  sudo gem install cocoapods   # if not already installed
  npx cap sync ios             # runs pod install for you
  ```

- Backend CORS (`app/backend/api/main.py`) allows `capacitor://localhost`
  (iOS) and `https://localhost` (Android) in addition to the local dev
  server origins.

## Day-to-day workflow

```bash
cd app/frontend/react_app
npm run cap:sync          # vite build, then copies dist/ into android/ and ios/
npm run cap:open:android  # opens the project in Android Studio
npm run cap:open:ios      # opens the project in Xcode (macOS + Xcode required)
```

Run `cap:sync` after every change you want reflected on-device — Capacitor
does not hot-reload the bundled build automatically the way `npm run dev`
does in a browser.

## Pointing the app at a backend

The API base URL is baked into the JS bundle at build time via
`VITE_API_BASE_URL`, the same variable used for the web build. `localhost`
means something different depending on where the app is actually running,
so pick the right value before running `cap:sync`:

| Target | `VITE_API_BASE_URL` |
| --- | --- |
| iOS Simulator | `http://localhost:8001` (simulator shares the host's network) |
| Android Emulator | `http://10.0.2.2:8001` (`10.0.2.2` is the emulator's alias for the host machine) |
| Physical device (either OS) | `http://<your-machine's-LAN-IP>:8001`, and the backend must be started with `--host 0.0.0.0` |

```bash
VITE_API_BASE_URL=http://10.0.2.2:8001 npm run cap:sync
```

## HTTP vs HTTPS

Both platforms restrict plain HTTP by default:

- **Android** blocks cleartext traffic on API 28+. `capacitor.config.ts`
  currently sets `android.allowMixedContent: true` so local HTTP backends
  work during development. Turn this off before a real release, once the
  backend is served over HTTPS.
- **iOS** App Transport Security blocks non-HTTPS requests. For local
  development against an HTTP backend, add an ATS exception for your dev
  host in `ios/App/App/Info.plist` (`NSAppTransportSecurity` /
  `NSExceptionDomains`). Don't ship that exception in a release build —
  point production builds at an HTTPS backend instead.

## Building a release

Release signing (Android keystore, iOS provisioning profile/certificate) and
store submission are unconfigured — this setup only covers local
development builds. That's a separate task once you're ready to distribute
the app.
