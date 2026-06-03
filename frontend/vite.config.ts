import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const customEmojiAssetPatterns = ["**/*.tgs", "**/*.webp", "**/*.webm"];
const DEFAULT_BACKEND_ORIGIN = "http://127.0.0.1:8000";

const normalizeOrigin = (
  value: string | undefined,
  defaultProtocol: "http" | "ws",
) => {
  const raw = String(value ?? "")
    .trim()
    .replace(/\/+$/, "");
  if (!raw) return null;

  const url = new URL(
    /^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : `${defaultProtocol}://${raw}`,
  );
  url.pathname = "";
  url.search = "";
  url.hash = "";
  return url.origin;
};

const toWsOrigin = (httpOrigin: string) => {
  const url = new URL(httpOrigin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.origin;
};

const normalizeAssetBase = (value: string | undefined) => {
  const raw = String(value ?? "").trim();
  if (!raw) {
    return "/";
  }

  return raw.endsWith("/") ? raw : `${raw}/`;
};

const toKebabChunkName = (value: string) =>
  value
    .replace(/\.[^.]+$/, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();

const getManualChunk = (id: string) => {
  const normalizedId = id.replaceAll("\\", "/");

  if (normalizedId.includes("/node_modules/react-router-dom/")) {
    return "vendor-router";
  }
  if (
    normalizedId.includes("/node_modules/react/") ||
    normalizedId.includes("/node_modules/react-dom/")
  ) {
    return "vendor-react";
  }
  if (
    normalizedId.includes("/node_modules/lottie-web/") ||
    normalizedId.includes("/node_modules/fflate/") ||
    normalizedId.includes("/node_modules/react-easy-crop/")
  ) {
    return "vendor-media";
  }
  if (
    normalizedId.includes("/node_modules/axios/") ||
    normalizedId.includes("/node_modules/zod/")
  ) {
    return "vendor-api";
  }

  const pageMatch = normalizedId.match(/\/src\/pages\/([^/]+Page)\.tsx$/);
  if (pageMatch?.[1]) {
    return `page-${toKebabChunkName(pageMatch[1])}`;
  }

  return undefined;
};

const getAssetFileName = (assetName: string | undefined) => {
  if (/\.(?:tgs|webp|webm)$/i.test(assetName ?? "")) {
    return "assets/custom-emoji/[name]-[hash][extname]";
  }

  if (/\.(?:png|jpe?g|gif|svg|avif)$/i.test(assetName ?? "")) {
    return "assets/images/[name]-[hash][extname]";
  }

  if (/\.(?:woff2?|ttf|otf)$/i.test(assetName ?? "")) {
    return "assets/fonts/[name]-[hash][extname]";
  }

  return "assets/[name]-[hash][extname]";
};

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const enablePwa = String(env.VITE_ENABLE_PWA ?? "").trim() === "1";
  const backendOrigin =
    normalizeOrigin(env.VITE_BACKEND_ORIGIN, "http") ?? DEFAULT_BACKEND_ORIGIN;
  const backendWsOrigin =
    normalizeOrigin(env.VITE_WS_BACKEND_ORIGIN, "ws") ??
    toWsOrigin(backendOrigin);

  return {
    assetsInclude: customEmojiAssetPatterns,
    base: normalizeAssetBase(env.VITE_ASSET_BASE_URL),
    build: {
      rollupOptions: {
        output: {
          assetFileNames: (assetInfo) => getAssetFileName(assetInfo.name),
          chunkFileNames: "assets/chunks/[name]-[hash].js",
          entryFileNames: "assets/entry/[name]-[hash].js",
          manualChunks: getManualChunk,
        },
      },
    },
    plugins: [
      react({
        babel: {
          plugins: [["babel-plugin-react-compiler"]],
        },
      }),
      ...(enablePwa
        ? [
            VitePWA({
              strategies: "injectManifest",
              srcDir: "src",
              filename: "sw.ts",
              injectRegister: null,
              registerType: "autoUpdate",
              devOptions: {
                enabled: false,
              },
              manifest: {
                name: "Devil",
                short_name: "Devil",
                start_url: "/",
                display: "standalone",
                background_color: "#0a1020",
                theme_color: "#0a1020",
                icons: [],
              },
            }),
          ]
        : []),
    ],

    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,

      headers: {
        "Cross-Origin-Opener-Policy": "same-origin-allow-popups",
      },

      proxy: {
        "/api": {
          target: backendOrigin,
          changeOrigin: true,
        },
        "/ws": {
          target: backendWsOrigin,
          ws: true,
          changeOrigin: true,
          secure: false,
          rewriteWsOrigin: true,
          configure: (proxy) => {
            proxy.on("error", (error) => {
              const code = (error as NodeJS.ErrnoException).code;
              if (
                code === "ECONNABORTED" ||
                code === "ECONNRESET" ||
                code === "EPIPE"
              ) {
                return;
              }
              console.error("[vite][ws-proxy] unexpected error", error);
            });
          },
        },
      },
    },
  };
});
