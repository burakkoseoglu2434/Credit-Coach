type VisualFlowProps = {
  steps: Array<{
    title: string;
    body: string;
  }>;
};

export function VisualFlow({ steps }: VisualFlowProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      {steps.map((step, index) => (
        <div key={step.title} className="relative">
          <div className="panel h-full p-5">
            <div className="text-xs uppercase tracking-[0.22em] text-arctic/55">
              {index + 1}
            </div>
            <div className="mt-3 font-display text-xl font-semibold text-white">{step.title}</div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{step.body}</p>
          </div>
          {index < steps.length - 1 ? (
            <div className="absolute -right-2 top-1/2 hidden h-px w-4 bg-cobalt/40 lg:block" />
          ) : null}
        </div>
      ))}
    </div>
  );
}
