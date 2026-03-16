import type { Express, Request, Response } from "express";

import {
  contactRequestSchema,
  demoRequestSchema,
  investorRequestSchema,
} from "../shared/content-schema.js";
import {
  saveContactRequest,
  saveDemoRequest,
  saveInvestorRequest,
} from "./storage/inbound.js";
import { getDemoIndex, getDemoPayload } from "./services/demo-data.js";

function handleZodError(error: unknown, res: Response) {
  if (typeof error === "object" && error !== null && "issues" in error) {
    return res.status(400).json({
      ok: false,
      message: "Validation failed.",
      details: (error as { issues?: unknown }).issues ?? [],
    });
  }

  return res.status(500).json({
    ok: false,
    message: "Unexpected error.",
  });
}

export function registerRoutes(app: Express) {
  app.get("/api/health", (_req, res) => {
    res.json({
      ok: true,
      company: "Kuantitive",
      product: "credit-coach",
      service: "website",
    });
  });

  app.get("/api/demo/index", (_req, res) => {
    res.json(getDemoIndex());
  });

  app.get("/api/demo/:slug", async (req, res) => {
    const payload = await getDemoPayload(req.params.slug);
    if (!payload) {
      return res.status(404).json({
        ok: false,
        message: "Demo snapshot not found.",
      });
    }

    return res.json(payload);
  });

  app.post("/api/contact", async (req: Request, res: Response) => {
    try {
      const payload = contactRequestSchema.parse({
        ...req.body,
        inquiryType: "contact",
      });
      const result = await saveContactRequest(payload);
      return res.status(201).json({
        ok: true,
        message: "Contact request saved.",
        storageMode: result.mode,
      });
    } catch (error) {
      return handleZodError(error, res);
    }
  });

  app.post("/api/demo-request", async (req: Request, res: Response) => {
    try {
      const payload = demoRequestSchema.parse({
        ...req.body,
        inquiryType: "demo",
      });
      const result = await saveDemoRequest(payload);
      return res.status(201).json({
        ok: true,
        message: "Demo request saved.",
        storageMode: result.mode,
      });
    } catch (error) {
      return handleZodError(error, res);
    }
  });

  app.post("/api/investor-request", async (req: Request, res: Response) => {
    try {
      const payload = investorRequestSchema.parse({
        ...req.body,
        inquiryType: "investor",
      });
      const result = await saveInvestorRequest(payload);
      return res.status(201).json({
        ok: true,
        message: "Investor inquiry saved.",
        storageMode: result.mode,
      });
    } catch (error) {
      return handleZodError(error, res);
    }
  });
}
