import {
  DefaultOptionType,
  Icons,
  Select,
  SelectProps,
  Space,
  SparkleIcon,
} from "fidesui";
import { uniq } from "lodash";
import { useMemo } from "react";

const ALL_SUGGESTED_VALUE = "all-suggested";

interface DataUseSelectWithSuggestionsProps extends Omit<
  SelectProps,
  "options" | "value" | "onChange" | "mode"
> {
  options: DefaultOptionType[];
  suggestedDataUses: string[];
  value?: string[];
  onChange?: (value: string[]) => void;
}

export const DataUseSelectWithSuggestions = ({
  options,
  suggestedDataUses,
  value,
  onChange,
  ...props
}: DataUseSelectWithSuggestionsProps) => {
  const handleChange = (next: string[]) => {
    if (next.includes(ALL_SUGGESTED_VALUE)) {
      const merged = uniq([
        ...suggestedDataUses,
        ...next.filter((v) => v !== ALL_SUGGESTED_VALUE),
      ]);
      onChange?.(merged);
    } else {
      onChange?.(next);
    }
  };

  const optionsGroups = useMemo(() => {
    const suggestedOptions: DefaultOptionType[] = [];
    const allOptions: DefaultOptionType[] = [];
    options?.forEach((opt) => {
      if (suggestedDataUses.includes(opt.value as string)) {
        suggestedOptions.push(opt);
      } else {
        allOptions.push(opt);
      }
    });
    return {
      suggested: suggestedOptions,
      all: allOptions,
    };
  }, [options, suggestedDataUses]);

  const optionsToRender = optionsGroups.suggested.length
    ? [
        {
          label: "Select all suggested",
          value: ALL_SUGGESTED_VALUE,
        },
        {
          label: (
            <Space>
              <SparkleIcon size={14} />
              <span>Suggested data uses</span>
            </Space>
          ),
          value: "suggested",
          options: optionsGroups.suggested,
        },
        {
          label: (
            <Space>
              <Icons.Document />
              <span>All data uses</span>
            </Space>
          ),
          value: "all",
          options: optionsGroups.all,
        },
      ]
    : optionsGroups.all;

  return (
    <Select
      {...props}
      mode="multiple"
      placeholder="Select data uses"
      allowClear
      options={optionsToRender}
      value={value}
      onChange={handleChange}
    />
  );
};
