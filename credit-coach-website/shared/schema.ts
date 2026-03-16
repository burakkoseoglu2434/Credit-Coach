import { relations } from "drizzle-orm";
import { pgTable, serial, text, timestamp, varchar } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";

export const contactRequests = pgTable("contact_requests", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  company: varchar("company", { length: 160 }).notNull(),
  role: varchar("role", { length: 120 }).notNull(),
  email: varchar("email", { length: 180 }).notNull(),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const demoRequests = pgTable("demo_requests", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  company: varchar("company", { length: 160 }).notNull(),
  role: varchar("role", { length: 120 }).notNull(),
  email: varchar("email", { length: 180 }).notNull(),
  useCase: text("use_case").notNull(),
  teamSize: varchar("team_size", { length: 40 }).notNull(),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const investorRequests = pgTable("investor_requests", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  company: varchar("company", { length: 160 }).notNull(),
  role: varchar("role", { length: 120 }).notNull(),
  email: varchar("email", { length: 180 }).notNull(),
  fundName: varchar("fund_name", { length: 180 }).notNull(),
  focusArea: text("focus_area").notNull(),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const demoSnapshots = pgTable("demo_snapshots", {
  id: serial("id").primaryKey(),
  slug: varchar("slug", { length: 120 }).notNull(),
  title: varchar("title", { length: 180 }).notNull(),
  category: varchar("category", { length: 120 }).notNull(),
  sourceRunId: varchar("source_run_id", { length: 120 }),
  sourceArtifact: varchar("source_artifact", { length: 240 }),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const demoSnapshotsRelations = relations(demoSnapshots, () => ({}));

export const insertContactRequestSchema = createInsertSchema(contactRequests);
export const insertDemoRequestSchema = createInsertSchema(demoRequests);
export const insertInvestorRequestSchema = createInsertSchema(investorRequests);
