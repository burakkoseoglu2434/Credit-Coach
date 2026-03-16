import cors from "cors";
import express from "express";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { registerRoutes } from "./routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const isProduction = process.env.NODE_ENV === "production";

async function createApp() {
  const app = express();

  app.use(cors());
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  registerRoutes(app);

  if (!isProduction) {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      root: rootDir,
      server: { middlewareMode: true },
      appType: "spa",
    });

    app.use(vite.middlewares);
    app.use("*", async (req, res, next) => {
      try {
        const url = req.originalUrl;
        const template = await fs.readFile(path.resolve(rootDir, "index.html"), "utf-8");
        const transformed = await vite.transformIndexHtml(url, template);
        res.status(200).set({ "Content-Type": "text/html" }).end(transformed);
      } catch (error) {
        vite.ssrFixStacktrace(error as Error);
        next(error);
      }
    });
    return app;
  }

  const clientDir = path.resolve(rootDir, "dist", "client");
  app.use(express.static(clientDir));
  app.use("*", (_req, res) => {
    res.sendFile(path.resolve(clientDir, "index.html"));
  });

  return app;
}

createApp()
  .then((app) => {
    const port = Number(process.env.PORT || 3000);
    app.listen(port, () => {
      // eslint-disable-next-line no-console
      console.log(`credit-coach-website listening on http://localhost:${port}`);
    });
  })
  .catch((error) => {
    // eslint-disable-next-line no-console
    console.error(error);
    process.exit(1);
  });
