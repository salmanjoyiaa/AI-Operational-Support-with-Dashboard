import react from "@vitejs/plugin-react";
import { build } from "vite";

await build({
  root: process.cwd(),
  configFile: false,
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
