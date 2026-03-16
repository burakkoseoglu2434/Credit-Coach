import { z } from "zod";

const baseInquirySchema = z.object({
  name: z.string().min(2, "Please enter a name."),
  company: z.string().min(2, "Please enter a company name."),
  role: z.string().min(2, "Please enter your role."),
  email: z.string().email("Please enter a valid email."),
  message: z.string().min(20, "Please share a bit more context."),
});

export const contactRequestSchema = baseInquirySchema.extend({
  inquiryType: z.literal("contact"),
});

export const demoRequestSchema = baseInquirySchema.extend({
  inquiryType: z.literal("demo"),
  useCase: z.string().min(4, "Please describe the primary use case."),
  teamSize: z.string().min(1, "Please select a team size."),
});

export const investorRequestSchema = baseInquirySchema.extend({
  inquiryType: z.literal("investor"),
  fundName: z.string().min(2, "Please enter a fund or firm name."),
  focusArea: z.string().min(3, "Please share your focus area."),
});

export const inboundRequestSchema = z.discriminatedUnion("inquiryType", [
  contactRequestSchema,
  demoRequestSchema,
  investorRequestSchema,
]);

export type ContactRequest = z.infer<typeof contactRequestSchema>;
export type DemoRequest = z.infer<typeof demoRequestSchema>;
export type InvestorRequest = z.infer<typeof investorRequestSchema>;
export type InboundRequest = z.infer<typeof inboundRequestSchema>;
