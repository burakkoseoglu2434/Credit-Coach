export const navLinks = [
  { href: "/product", label: "Product" },
  { href: "/modules", label: "Modules" },
  { href: "/demo", label: "Demo Center" },
  { href: "/proof", label: "Proof" },
  { href: "/investor", label: "Investor" },
  { href: "/contact", label: "Contact" },
];

export const modules = [
  {
    title: "Risk & Explainability",
    description:
      "Moves the credit flow beyond approve / deny by exposing why a customer is off-policy and what can shift risk safely.",
    output: "risk drivers, decision rationale, PD context",
    artifact: "batch_summary.json",
  },
  {
    title: "Recourse Planning",
    description:
      "Generates real-world action plans instead of abstract feature edits, across behavioral, structural, and institutional levers.",
    output: "customer roadmap, phased actions, action mix",
    artifact: "customer_roadmap.json",
  },
  {
    title: "Behavior-Aware Ranking",
    description:
      "Scores plans by both expected impact and likelihood of execution, so recommendations stay grounded in real borrower behavior.",
    output: "execution probability, expected PD improvement",
    artifact: "behavior_aware_summary.json",
  },
  {
    title: "Sequential Trajectories",
    description:
      "Builds phase-based improvement paths with 4w, 12w, and 24w checkpoints instead of forcing a one-shot plan.",
    output: "trajectory health, checkpoint performance, replan signals",
    artifact: "trajectory_summary.json",
  },
  {
    title: "Offer Optimization",
    description:
      "Adds institution-side offers into the same decision surface and optimizes them against approval, default, and margin proxies.",
    output: "offer mix, acceptance probability, recovery proxy deltas",
    artifact: "offer_optimization_summary.json",
  },
  {
    title: "Learning Loop",
    description:
      "Logs decision context, tracks delayed outcomes, and produces confidence-aware off-policy learning signals for future policy improvement.",
    output: "decision coverage, reward coverage, OPE confidence",
    artifact: "off_policy_evaluation.json",
  },
  {
    title: "Governance & Release Evidence",
    description:
      "Keeps fairness, reliability, telemetry, and acceptance evidence explicit so recommendations never outrun governance.",
    output: "acceptance summary, release pack, human-readable review",
    artifact: "milestone_acceptance_summary.json",
  },
];

export const processSteps = [
  {
    title: "Diagnose the decline",
    body: "Credit Coach starts with risk, explanation, and segment context rather than treating every denied applicant as the same problem.",
  },
  {
    title: "Generate feasible next steps",
    body: "The engine produces behavioral, structural, and institutional actions that can be sequenced over time.",
  },
  {
    title: "Filter through governance",
    body: "Fairness, reliability, telemetry, and operational controls stay upstream of any recommendation or promotion decision.",
  },
  {
    title: "Optimize the commercial path",
    body: "Institution-side offers can join customer actions in the same plan when they improve recovery proxies without violating governance.",
  },
  {
    title: "Learn from outcomes",
    body: "Decision logs, delayed outcomes, and off-policy evaluation close the loop so policy improvement becomes evidence-based.",
  },
];

export const investorHighlights = [
  "This is not just a scoring model. It is a decision-intelligence layer that sits after deny and before lost customer value.",
  "The strongest wedge is lender recovery of denied or near-prime customers under governance constraints.",
  "The technical core already exists: recommendation quality, behavior-aware ranking, phased trajectories, offer optimization, and learning-loop evidence are shipped.",
  "The commercial gap is productization, operator surfaces, and go-to-market packaging, which is exactly where a website and product shell become strategically useful.",
];
