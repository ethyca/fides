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
      value: PropagationPolicyKeyEnum.CASCADE_DOWN_OPT_OUT,
      label: "Cascade down opt out",
    },
    {
      value: PropagationPolicyKeyEnum.CASCADE_DOWN_ALL,
      label: "Cascade down all",
    },
    { value: PropagationPolicyKeyEnum.CASCADE_UP_ALL, label: "Cascade up all" },
    {
      value: PropagationPolicyKeyEnum.CASCADE_UP_ALL_CASCADE_DOWN_ALL,
      label: "Cascade up and down all",
    },
    {
      value: PropagationPolicyKeyEnum.CASCADE_DOWN_ALL_CASCADE_UP_OPT_IN,
      label: "Cascade down all, cascade up opt in",
    },
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
        style={{ width: 320 }}
        placeholder="Cascade down opt out"
        allowClear
        options={options}
        aria-labelledby="policy-select-label"
      />
    </Flex>
  );
};

export default PropagationPolicyDropdown;
