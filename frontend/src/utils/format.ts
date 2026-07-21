export const formatScore = (value: number | null): string =>
  value === null ? '—' : Math.round(value).toString();

export const formatCurrency = (value: number | null): string => {
  if (value === null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: value < 10 ? 2 : 2,
    maximumFractionDigits: value < 10 ? 3 : 2,
  }).format(value);
};

export const formatPercent = (value: number | null, digits = 2): string => {
  if (value === null) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(digits)}%`;
};

export const formatCompact = (value: number | null): string => {
  if (value === null) return '—';
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

export const formatDate = (value: string | null): string => {
  if (!value) return 'Unavailable';
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${value}T12:00:00Z`));
};

export const formatDateTime = (value: string): string =>
  new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(new Date(value));
