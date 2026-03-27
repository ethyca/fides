import { Flex, Form, Select } from "fidesui";

import SearchInput from "~/features/common/SearchInput";

const STATUS_OPTIONS = [
  { label: "All statuses", value: "" },
  { label: "Enabled", value: "enabled" },
  { label: "Disabled", value: "disabled" },
  { label: "Has violations", value: "has_violations" },
  { label: "New", value: "new" },
];

const CONTROL_OPTIONS = [
  { label: "All controls", value: "" },
  { label: "GDPR", value: "gdpr" },
  { label: "PCI-DSS", value: "pci-dss" },
  { label: "PSD2", value: "psd2" },
  { label: "SOC 2", value: "soc2" },
];

const DATA_USE_OPTIONS = [
  { label: "All data uses", value: "" },
  { label: "Marketing", value: "marketing" },
  { label: "Analytics", value: "analytics" },
  { label: "Finance", value: "finance" },
  { label: "Operations", value: "operations" },
  { label: "HR", value: "hr" },
];

interface PoliciesToolbarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
}

const PoliciesToolbar = ({
  searchValue,
  onSearchChange,
}: PoliciesToolbarProps) => (
  <Form layout="inline" className="mb-6 flex grow gap-2">
    <Flex className="grow self-stretch">
      <Form.Item name="search" className="!me-0">
        <SearchInput
          value={searchValue}
          onChange={onSearchChange}
          placeholder="Search policies..."
        />
      </Form.Item>
    </Flex>
    <Form.Item className="!me-0 self-end">
      <Select
        aria-label="Status"
        placeholder="Status"
        options={STATUS_OPTIONS}
        className="min-w-[280px]"
        allowClear
      />
    </Form.Item>
    <Form.Item className="!me-0 self-end">
      <Select
        aria-label="Control"
        placeholder="Control"
        options={CONTROL_OPTIONS}
        className="min-w-[280px]"
        allowClear
      />
    </Form.Item>
    <Form.Item className="!me-0 self-end">
      <Select
        aria-label="Data use"
        placeholder="Data use"
        options={DATA_USE_OPTIONS}
        className="min-w-[280px]"
        allowClear
      />
    </Form.Item>
  </Form>
);

export default PoliciesToolbar;
