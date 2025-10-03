import {
  AntAlert as Alert,
  AntInputNumber as InputNumber,
  AntSelect as Select,
  AntSpace as Space,
  AntTimePicker as TimePicker,
  AntTypography as Typography,
} from "fidesui";
import dayjs, { Dayjs } from "dayjs";
import { useEffect, useState } from "react";

import {
  DAY_OF_WEEK_LABELS,
  DayOfWeek,
  Frequency,
  generateCronExpression,
  getScheduleDescription,
  isValidDayOfMonth,
  parseCronExpression,
  type ScheduleConfig,
} from "../helpers/cronHelpers";

const { Text } = Typography;

interface DigestSchedulePickerProps {
  value?: string; // Cron expression
  onChange?: (value: string) => void;
}

const FREQUENCY_OPTIONS = [
  { label: "Daily", value: Frequency.DAILY },
  { label: "Weekly", value: Frequency.WEEKLY },
  { label: "Weekdays", value: Frequency.WEEKDAYS },
  { label: "Monthly", value: Frequency.MONTHLY },
];

const DAY_OF_WEEK_OPTIONS = Object.entries(DAY_OF_WEEK_LABELS).map(
  ([value, label]) => ({
    label,
    value: parseInt(value, 10),
  }),
);

const DigestSchedulePicker = ({
  value,
  onChange,
}: DigestSchedulePickerProps) => {
  const [frequency, setFrequency] = useState<Frequency>(Frequency.WEEKLY);
  const [time, setTime] = useState<Dayjs>(dayjs().hour(9).minute(0));
  const [dayOfWeek, setDayOfWeek] = useState<DayOfWeek>(DayOfWeek.MONDAY);
  const [dayOfMonth, setDayOfMonth] = useState<number>(1);
  const [showCustomCronWarning, setShowCustomCronWarning] = useState(false);

  // Parse incoming cron expression when value changes
  useEffect(() => {
    if (value) {
      const parsed = parseCronExpression(value);
      if (parsed) {
        setShowCustomCronWarning(false);
        setFrequency(parsed.frequency);
        const [hour, minute] = parsed.time.split(":").map(Number);
        setTime(dayjs().hour(hour).minute(minute));
        if (parsed.dayOfWeek !== undefined) {
          setDayOfWeek(parsed.dayOfWeek);
        }
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
      time: time.format("HH:mm"),
      ...(frequency === Frequency.WEEKLY && { dayOfWeek }),
      ...(frequency === Frequency.MONTHLY && { dayOfMonth }),
    };

    try {
      const cron = generateCronExpression(config);
      onChange?.(cron);
    } catch (error) {
      // Invalid configuration, don't update
      console.error("Error generating cron expression:", error);
    }
  }, [frequency, time, dayOfWeek, dayOfMonth, onChange]);

  const handleDayOfMonthChange = (val: number | null) => {
    if (val !== null && isValidDayOfMonth(val)) {
      setDayOfMonth(val);
    }
  };

  const scheduleConfig: ScheduleConfig = {
    frequency,
    time: time.format("HH:mm"),
    ...(frequency === Frequency.WEEKLY && { dayOfWeek }),
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

      <div className="flex gap-4">
        <div className="flex-1">
          <Text strong className="mb-1 block">
            Frequency
          </Text>
          <Select
            value={frequency}
            onChange={setFrequency}
            options={FREQUENCY_OPTIONS}
            data-testid="select-frequency"
            className="w-full"
          />
        </div>

        <div className="flex-1">
          <Text strong className="mb-1 block">
            Time (UTC)
          </Text>
          <TimePicker
            value={time}
            onChange={(val) => val && setTime(val)}
            format="HH:mm"
            showNow={false}
            data-testid="time-picker"
            className="w-full"
          />
        </div>
      </div>

      {frequency === Frequency.WEEKLY && (
        <div>
          <Text strong className="mb-1 block">
            Day of Week
          </Text>
          <Select
            value={dayOfWeek}
            onChange={setDayOfWeek}
            options={DAY_OF_WEEK_OPTIONS}
            data-testid="select-day-of-week"
            className="w-full"
          />
        </div>
      )}

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
          Schedule: {getScheduleDescription(scheduleConfig)}
        </Text>
      </div>
    </Space>
  );
};

export default DigestSchedulePicker;
