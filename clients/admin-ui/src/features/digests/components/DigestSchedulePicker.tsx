import { format } from "date-fns-tz";
import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import {
  AntAlert as Alert,
  AntInputNumber as InputNumber,
  AntSelect as Select,
  AntSpace as Space,
  AntTypography as Typography,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import {
  DayOfWeek,
  Frequency,
  generateCronExpression,
  getScheduleDescription,
  isValidDayOfMonth,
  parseCronExpression,
  type ScheduleConfig,
} from "../helpers/cronHelpers";

// Extend dayjs with timezone support
dayjs.extend(utc);
dayjs.extend(timezone);

const { Text } = Typography;

// Hardcoded values
const FIXED_TIME = "09:00"; // 9:00 AM
const FIXED_DAY_OF_WEEK = DayOfWeek.MONDAY;

interface DigestSchedulePickerProps {
  value?: string; // Cron expression
  onChange?: (value: string) => void;
  onTimezoneChange?: (timezone: string) => void;
  timezone?: string; // Stored timezone (for edit mode)
}

const FREQUENCY_OPTIONS = [
  { label: "Daily", value: Frequency.DAILY },
  { label: "Weekly", value: Frequency.WEEKLY },
  { label: "Weekdays", value: Frequency.WEEKDAYS },
  { label: "Monthly", value: Frequency.MONTHLY },
];

const DigestSchedulePicker = ({
  value,
  onChange,
  onTimezoneChange,
  timezone: timezoneProp,
}: DigestSchedulePickerProps) => {
  const [frequency, setFrequency] = useState<Frequency>(Frequency.WEEKLY);
  const [dayOfMonth, setDayOfMonth] = useState<number>(1);
  const [showCustomCronWarning, setShowCustomCronWarning] = useState(false);

  // Get browser timezone
  const browserTimezone = dayjs.tz.guess();

  // Use stored timezone if provided (edit mode), otherwise use browser timezone (create mode)
  const effectiveTimezone = timezoneProp || browserTimezone;

  // Get timezone display info: city name and GMT offset
  const timezoneInfo = useMemo(() => {
    const now = new Date();
    // Get GMT offset in format like "GMT-3" or "GMT+5:30"
    const gmtOffset = format(now, "O", { timeZone: effectiveTimezone });

    // Get a display name for the timezone (last part of timezone string)
    // e.g., "America/Argentina/Buenos_Aires" → "Buenos Aires"
    const timezoneParts = effectiveTimezone.split("/");
    const cityName = timezoneParts[timezoneParts.length - 1].replace(/_/g, " ");

    return { cityName, gmtOffset };
  }, [effectiveTimezone]);

  // Notify parent of timezone on mount and when it changes
  // Only update when creating new (no timezone prop) or when browser timezone changes
  useEffect(() => {
    if (!timezoneProp) {
      onTimezoneChange?.(browserTimezone);
    }
  }, [browserTimezone, onTimezoneChange, timezoneProp]);

  // Parse incoming cron expression when value changes
  useEffect(() => {
    if (value) {
      const parsed = parseCronExpression(value);
      if (parsed) {
        setShowCustomCronWarning(false);
        setFrequency(parsed.frequency);
        if (parsed.dayOfMonth !== undefined) {
          setDayOfMonth(parsed.dayOfMonth);
        }
      } else {
        // Cron expression doesn't match our patterns
        setShowCustomCronWarning(true);
      }
    }
  }, [value]);

  // Generate cron expression when any field changes
  useEffect(() => {
    const config: ScheduleConfig = {
      frequency,
      time: FIXED_TIME,
      ...(frequency === Frequency.WEEKLY && { dayOfWeek: FIXED_DAY_OF_WEEK }),
      ...(frequency === Frequency.MONTHLY && { dayOfMonth }),
    };

    try {
      const cron = generateCronExpression(config);
      onChange?.(cron);
    } catch (error) {
      // Invalid configuration, don't update
      // eslint-disable-next-line no-console
      console.error("Error generating cron expression:", error);
    }
  }, [frequency, dayOfMonth, onChange]);

  const handleDayOfMonthChange = (val: number | null) => {
    if (val !== null && isValidDayOfMonth(val)) {
      setDayOfMonth(val);
    }
  };

  const scheduleConfig: ScheduleConfig = {
    frequency,
    time: FIXED_TIME,
    ...(frequency === Frequency.WEEKLY && { dayOfWeek: FIXED_DAY_OF_WEEK }),
    ...(frequency === Frequency.MONTHLY && { dayOfMonth }),
  };

  return (
    <Space direction="vertical" size="middle" className="w-full">
      {showCustomCronWarning && (
        <Alert
          message="Custom Cron Expression"
          description="This digest uses a custom cron expression that cannot be edited with the picker. Changing the schedule will replace the custom expression."
          type="warning"
          closable
          onClose={() => setShowCustomCronWarning(false)}
        />
      )}

      <div>
        <Text strong className="mb-1 block">
          Frequency
        </Text>
        <Select
          value={frequency}
          onChange={setFrequency}
          options={FREQUENCY_OPTIONS}
          data-testid="select-frequency"
          className="w-full"
          id="select-frequency"
          aria-label="Frequency"
        />
      </div>

      {frequency === Frequency.MONTHLY && (
        <div>
          <Text strong className="mb-1 block">
            Day of Month
          </Text>
          <InputNumber
            value={dayOfMonth}
            onChange={handleDayOfMonthChange}
            min={1}
            max={31}
            data-testid="input-day-of-month"
            className="w-full"
          />
          {dayOfMonth > 28 && (
            <Text type="secondary" className="mt-1 block text-xs">
              Note: Days 29-31 will not trigger in all months
            </Text>
          )}
        </div>
      )}

      <div className="rounded-md bg-gray-50 p-3">
        <Text type="secondary" className="text-xs">
          Schedule: {getScheduleDescription(scheduleConfig)}{" "}
          {timezoneInfo.cityName} ({timezoneInfo.gmtOffset})
        </Text>
      </div>
    </Space>
  );
};

export default DigestSchedulePicker;
