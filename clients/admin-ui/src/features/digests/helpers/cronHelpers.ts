/**
 * Helper functions for converting between user-friendly frequency selections
 * and cron expressions
 */

import dayjs from "dayjs";

export enum Frequency {
  DAILY = "daily",
  WEEKLY = "weekly",
  WEEKDAYS = "weekdays",
  MONTHLY = "monthly",
}

export enum DayOfWeek {
  SUNDAY = 0,
  MONDAY = 1,
  TUESDAY = 2,
  WEDNESDAY = 3,
  THURSDAY = 4,
  FRIDAY = 5,
  SATURDAY = 6,
}

export const DAY_OF_WEEK_LABELS: Record<DayOfWeek, string> = {
  [DayOfWeek.SUNDAY]: "Sunday",
  [DayOfWeek.MONDAY]: "Monday",
  [DayOfWeek.TUESDAY]: "Tuesday",
  [DayOfWeek.WEDNESDAY]: "Wednesday",
  [DayOfWeek.THURSDAY]: "Thursday",
  [DayOfWeek.FRIDAY]: "Friday",
  [DayOfWeek.SATURDAY]: "Saturday",
};

export interface ScheduleConfig {
  frequency: Frequency;
  time: string; // Format: "HH:mm" (24-hour)
  dayOfWeek?: DayOfWeek; // For weekly
  dayOfMonth?: number; // For monthly (1-31)
}

/**
 * Converts a schedule configuration to a cron expression
 * Cron format: minute hour day-of-month month day-of-week
 */
export const generateCronExpression = (config: ScheduleConfig): string => {
  const [hour, minute] = config.time.split(":").map(Number);

  switch (config.frequency) {
    case Frequency.DAILY:
      // Every day at specified time
      return `${minute} ${hour} * * *`;

    case Frequency.WEEKLY:
      // Specific day of week at specified time
      if (config.dayOfWeek === undefined) {
        throw new Error("Day of week is required for weekly frequency");
      }
      return `${minute} ${hour} * * ${config.dayOfWeek}`;

    case Frequency.WEEKDAYS:
      // Monday through Friday at specified time
      return `${minute} ${hour} * * 1-5`;

    case Frequency.MONTHLY:
      // Specific day of month at specified time
      if (config.dayOfMonth === undefined) {
        throw new Error("Day of month is required for monthly frequency");
      }
      return `${minute} ${hour} ${config.dayOfMonth} * *`;

    default:
      throw new Error(`Unsupported frequency: ${config.frequency}`);
  }
};

/**
 * Attempts to parse a cron expression back into a schedule configuration
 * Returns null if the cron expression doesn't match our supported patterns
 */
export const parseCronExpression = (
  cronExpression: string,
): ScheduleConfig | null => {
  const parts = cronExpression.trim().split(/\s+/);

  if (parts.length !== 5) {
    return null; // Invalid cron format
  }

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Validate minute and hour
  const minuteNum = parseInt(minute, 10);
  const hourNum = parseInt(hour, 10);

  if (
    Number.isNaN(minuteNum) ||
    Number.isNaN(hourNum) ||
    minuteNum < 0 ||
    minuteNum > 59 ||
    hourNum < 0 ||
    hourNum > 23
  ) {
    return null;
  }

  const time = `${String(hourNum).padStart(2, "0")}:${String(minuteNum).padStart(2, "0")}`;

  // Check for monthly pattern: specific day of month
  if (month === "*" && dayOfWeek === "*" && dayOfMonth !== "*") {
    const dayNum = parseInt(dayOfMonth, 10);
    if (Number.isNaN(dayNum) || dayNum < 1 || dayNum > 31) {
      return null;
    }
    return {
      frequency: Frequency.MONTHLY,
      time,
      dayOfMonth: dayNum,
    };
  }

  // Check for weekdays pattern: Monday-Friday (1-5)
  if (dayOfMonth === "*" && month === "*" && dayOfWeek === "1-5") {
    return {
      frequency: Frequency.WEEKDAYS,
      time,
    };
  }

  // Check for weekly pattern: specific day of week
  if (dayOfMonth === "*" && month === "*" && dayOfWeek !== "*") {
    const dayNum = parseInt(dayOfWeek, 10);
    if (Number.isNaN(dayNum) || dayNum < 0 || dayNum > 6) {
      return null;
    }
    return {
      frequency: Frequency.WEEKLY,
      time,
      dayOfWeek: dayNum as DayOfWeek,
    };
  }

  // Check for daily pattern: every day
  if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*") {
    return {
      frequency: Frequency.DAILY,
      time,
    };
  }

  // Doesn't match any of our supported patterns
  return null;
};

/**
 * Validates if a day of month is valid
 */
export const isValidDayOfMonth = (day: number): boolean => {
  return day >= 1 && day <= 31;
};

/**
 * Gets a user-friendly description of a schedule configuration
 */
export const getScheduleDescription = (config: ScheduleConfig): string => {
  // Parse 24-hour time and format to 12-hour with AM/PM
  const timeStr = dayjs(`2000-01-01 ${config.time}`).format("h:mm A");

  switch (config.frequency) {
    case Frequency.DAILY:
      return `Every day at ${timeStr}`;

    case Frequency.WEEKLY: {
      if (config.dayOfWeek === undefined) {
        return "";
      }
      return `Every ${DAY_OF_WEEK_LABELS[config.dayOfWeek]} at ${timeStr}`;
    }

    case Frequency.WEEKDAYS:
      return `Every weekday at ${timeStr}`;

    case Frequency.MONTHLY: {
      if (config.dayOfMonth === undefined) {
        return "";
      }
      // Determine the correct ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
      const day = config.dayOfMonth;
      const mod10 = day % 10;
      const mod100 = day % 100;
      let suffix = "th";
      if (mod10 === 1 && mod100 !== 11) {
        suffix = "st";
      } else if (mod10 === 2 && mod100 !== 12) {
        suffix = "nd";
      } else if (mod10 === 3 && mod100 !== 13) {
        suffix = "rd";
      }
      return `On the ${config.dayOfMonth}${suffix} of every month at ${timeStr}`;
    }

    default:
      return "";
  }
};

/**
 * Gets the frequency label from a cron expression
 * Returns "Custom" if the cron expression doesn't match our supported patterns
 */
export const getFrequencyLabel = (cronExpression: string): string => {
  const parsed = parseCronExpression(cronExpression);

  if (!parsed) {
    return "Custom";
  }

  switch (parsed.frequency) {
    case Frequency.DAILY:
      return "Daily";
    case Frequency.WEEKLY:
      return "Weekly";
    case Frequency.WEEKDAYS:
      return "Weekdays";
    case Frequency.MONTHLY:
      return "Monthly";
    default:
      return "Custom";
  }
};
