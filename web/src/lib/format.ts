const numberFormat = new Intl.NumberFormat("en-BD", { maximumFractionDigits: 0 });

export function quantity(value: number | undefined): string {
  return numberFormat.format(value ?? 0);
}

export function localTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function statusClass(status: string): string {
  return `status-${status.toLowerCase().replaceAll("_", "-")}`;
}

export function riskClass(level: string): string {
  return `risk-${level}`;
}
