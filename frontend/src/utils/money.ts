/** All amounts from the backend are integer minor units (paise). Never do
 * money math in floating point — these helpers only ever multiply/divide by
 * powers of ten for *display*; the backend is always the source of truth
 * for anything that affects a balance. */

export function minorToRupees(minor: number): number {
  return minor / 100;
}

export function rupeesToMinor(rupees: number): number {
  return Math.round(rupees * 100);
}

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatMinor(minor: number): string {
  return currencyFormatter.format(minorToRupees(minor));
}

export function formatMinorCompact(minor: number): string {
  const rupees = minorToRupees(minor);
  const abs = Math.abs(rupees);
  if (abs >= 100_000) return `₹${(rupees / 100_000).toFixed(1)}L`;
  if (abs >= 1_000) return `₹${(rupees / 1_000).toFixed(1)}K`;
  return `₹${rupees.toFixed(0)}`;
}
