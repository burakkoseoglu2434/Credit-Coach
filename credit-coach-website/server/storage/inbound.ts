import { db, databaseAvailable } from "../db.js";
import {
  contactRequests,
  demoRequests,
  investorRequests,
} from "../../shared/schema.js";
import type {
  ContactRequest,
  DemoRequest,
  InvestorRequest,
} from "../../shared/content-schema.js";

const memoryStore = {
  contact: [] as ContactRequest[],
  demo: [] as DemoRequest[],
  investor: [] as InvestorRequest[],
};

export async function saveContactRequest(payload: ContactRequest) {
  if (databaseAvailable && db) {
    await db.insert(contactRequests).values({
      name: payload.name,
      company: payload.company,
      role: payload.role,
      email: payload.email,
      message: payload.message,
    });
    return { persisted: true, mode: "database" as const };
  }

  memoryStore.contact.push(payload);
  return { persisted: true, mode: "memory" as const };
}

export async function saveDemoRequest(payload: DemoRequest) {
  if (databaseAvailable && db) {
    await db.insert(demoRequests).values({
      name: payload.name,
      company: payload.company,
      role: payload.role,
      email: payload.email,
      useCase: payload.useCase,
      teamSize: payload.teamSize,
      institutionType: payload.institutionType,
      portfolioFocus: payload.portfolioFocus,
      demoTrack: payload.demoTrack,
      timeline: payload.timeline,
      dataReadiness: payload.dataReadiness,
      message: payload.message,
    });
    return { persisted: true, mode: "database" as const };
  }

  memoryStore.demo.push(payload);
  return { persisted: true, mode: "memory" as const };
}

export async function saveInvestorRequest(payload: InvestorRequest) {
  if (databaseAvailable && db) {
    await db.insert(investorRequests).values({
      name: payload.name,
      company: payload.company,
      role: payload.role,
      email: payload.email,
      fundName: payload.fundName,
      focusArea: payload.focusArea,
      message: payload.message,
    });
    return { persisted: true, mode: "database" as const };
  }

  memoryStore.investor.push(payload);
  return { persisted: true, mode: "memory" as const };
}
