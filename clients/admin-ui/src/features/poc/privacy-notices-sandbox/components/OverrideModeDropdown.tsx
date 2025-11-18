import {
  AntFlex as Flex,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";

import type { OverrideMode } from "~/types/api/models/OverrideMode";
import { OverrideMode as OverrideModeEnum } from "~/types/api/models/OverrideMode";

interface OverrideModeDropdownProps {
  value: OverrideMode | null;
  onChange: (value: OverrideMode | null) => void;
}

const OverrideModeDropdown = ({
  value,
  onChange,
}: OverrideModeDropdownProps) => {
  const options = [
    { value: OverrideModeEnum.ANCESTORS, label: "Ancestors" },
    { value: OverrideModeEnum.DESCENDANTS, label: "Descendants" },
    { value: OverrideModeEnum.ALL, label: "All" },
  ];

  return (
    <Flex align="center" gap={3} className="mb-4">
      <label htmlFor="override-mode-select" id="override-mode-select-label">
        <Typography.Text strong style={{ whiteSpace: "nowrap" }}>
          Override mode:
        </Typography.Text>
      </label>
      <Select
        id="override-mode-select"
        value={value ?? undefined}
        onChange={(newValue) => {
          // Handle undefined (from clear action) or null
          onChange(newValue === undefined ? null : newValue);
        }}
        style={{ width: 200 }}
        placeholder="No override"
        allowClear
        options={options}
        aria-labelledby="override-mode-select-label"
      />
    </Flex>
  );
};

export default OverrideModeDropdown;
