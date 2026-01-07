import { Flex, Select, Typography } from "fidesui";

import type { PropagationPolicyKey } from "~/types/api/models/PropagationPolicyKey";
import { PropagationPolicyKey as PropagationPolicyKeyEnum } from "~/types/api/models/PropagationPolicyKey";

interface PropagationPolicyDropdownProps {
  value: PropagationPolicyKey | null;
  onChange: (value: PropagationPolicyKey | null) => void;
}

const PropagationPolicyDropdown = ({
  value,
  onChange,
}: PropagationPolicyDropdownProps) => {
  const options = [
    {
      value: PropagationPolicyKeyEnum.SYSTEM_ENFORCED,
      label: "System enforced",
    },
    { value: PropagationPolicyKeyEnum.CASCADE_DOWN, label: "Cascade down" },
    { value: PropagationPolicyKeyEnum.CASCADE_UP, label: "Cascade up" },
    {
      value: PropagationPolicyKeyEnum.CASCADE_UP_AND_DOWN,
      label: "Cascade up and down",
    },
    { value: PropagationPolicyKeyEnum.PREFER_OPT_IN, label: "Prefer opt in" },
  ];

  return (
    <Flex align="center" gap={3} className="mb-4">
      <label htmlFor="policy-select" id="policy-select-label">
        <Typography.Text strong style={{ whiteSpace: "nowrap" }}>
          Propagation policy:
        </Typography.Text>
      </label>
      <Select
        id="policy-select"
        value={value ?? undefined}
        onChange={(newValue) => {
          // Handle undefined (from clear action) or null
          onChange(newValue === undefined ? null : newValue);
        }}
        style={{ width: 200 }}
        placeholder="System enforced"
        allowClear
        options={options}
        aria-labelledby="policy-select-label"
      />
    </Flex>
  );
};

export default PropagationPolicyDropdown;
