import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./client/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#081225",
        ocean: "#0F2D68",
        cobalt: "#2052CC",
        arctic: "#D9E8FF",
        ink: "#0D1B32",
        mist: "#EAF2FF",
        signal: "#3DD9B4",
        copper: "#F0A24C",
        border: "rgba(142, 173, 255, 0.18)"
      },
      fontFamily: {
        display: ["\"Space Grotesk\"", "ui-sans-serif", "sans-serif"],
        body: ["\"Manrope\"", "ui-sans-serif", "sans-serif"],
      },
      boxShadow: {
        panel: "0 18px 60px rgba(8, 18, 37, 0.16)",
        glow: "0 0 0 1px rgba(109, 157, 255, 0.18), 0 18px 45px rgba(32, 82, 204, 0.20)",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top right, rgba(61, 217, 180, 0.14), transparent 34%), radial-gradient(circle at 12% 12%, rgba(32, 82, 204, 0.26), transparent 32%), linear-gradient(135deg, #081225 0%, #0C2046 42%, #102B63 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
