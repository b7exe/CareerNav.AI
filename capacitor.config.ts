import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ai.careernav.app',
  appName: 'CareerNav AI',
  webDir: 'static', // Placeholder for local assets
  server: {
    // 🔗 PASTE YOUR LIVE URL HERE (Render / Railway / etc.)
    // url: 'https://your-app-name.onrender.com', 
    cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#0A0F1C",
      showSpinner: true,
      androidScaleType: "CENTER_CROP"
    },
    StatusBar: {
      style: "DARK",
      backgroundColor: "#0A0F1C"
    }
  }
};

export default config;
