import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.triageai.esicarerouting',
  appName: 'TriageAI',
  webDir: 'dist',
  android: {
    // Local FastAPI dev backends usually run over plain HTTP; Android 9+
    // blocks cleartext traffic by default. Set false before a real release
    // once the backend is served over HTTPS.
    allowMixedContent: true
  }
};

export default config;
