export enum PollInterval {
  ONE_MINUTE = 60,
  FIVE_MINUTES = 300,
  FIFTEEN_MINUTES = 900,
  ONE_HOUR = 3600,
  SIX_HOURS = 21600,
  TWENTY_FOUR_HOURS = 86400,
}

export const POLL_INTERVAL_LABELS: Record<PollInterval, string> = {
  [PollInterval.ONE_MINUTE]: "Every minute",
  [PollInterval.FIVE_MINUTES]: "Every 5 minutes",
  [PollInterval.FIFTEEN_MINUTES]: "Every 15 minutes",
  [PollInterval.ONE_HOUR]: "Every hour",
  [PollInterval.SIX_HOURS]: "Every 6 hours",
  [PollInterval.TWENTY_FOUR_HOURS]: "Every 24 hours",
};

export const POLL_INTERVAL_OPTIONS = Object.entries(POLL_INTERVAL_LABELS).map(
  ([value, label]) => ({ value: Number(value), label }),
);
