import { InquiryForm } from "@/components/InquiryForm";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";

export function ContactPage() {
  return (
    <div>
      <PageHero
        eyebrow="Contact"
        title="Talk to Kuantitive about credit-coach."
        description="Use this page to request a product walkthrough, discuss a lender pilot, or start an investor conversation."
      />

      <section className="shell py-20">
        <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <SectionHeading
              eyebrow="Get in touch"
              title="The fastest way to move this forward is a focused conversation."
              description="Tell us whether you are exploring a lender use case, a live demo, or an investor discussion. The website backend is already set up to capture all three."
            />
            <div className="mt-8 grid gap-4">
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">For lenders</div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  Best when you want to discuss underwriting, recovery, recourse, or policy optimization use cases.
                </p>
              </div>
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">For investors</div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  Best when you want to see the wedge, the proof surface, and the next productization path.
                </p>
              </div>
            </div>
          </div>

          <InquiryForm />
        </div>
      </section>
    </div>
  );
}
