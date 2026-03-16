type BrandLogoProps = {
  className?: string;
};

export function BrandLogo({ className = "" }: BrandLogoProps) {
  return (
    <img
      src="/kuantitive-logo.svg"
      alt="Kuantitive logo"
      className={`h-auto w-full object-contain ${className}`.trim()}
      loading="eager"
      decoding="async"
    />
  );
}
