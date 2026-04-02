import { Flex, Form, Icons, Segmented, Select } from "fidesui";

import SearchInput from "~/features/common/SearchInput";

import { ControlGroup } from "./access-policies.slice";

export type ViewMode = "cards" | "table";

const STATUS_OPTIONS = [
  { label: "Enabled", value: "enabled" },
  { label: "Disabled", value: "disabled" },
];

interface PoliciesToolbarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  controlGroups: ControlGroup[];
  controlFilter: string | undefined;
  onControlFilterChange: (value: string | undefined) => void;
  enabledFilter: string | undefined;
  onEnabledFilterChange: (value: string | undefined) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

const PoliciesToolbar = ({
  searchValue,
  onSearchChange,
  controlGroups,
  controlFilter,
  onControlFilterChange,
  enabledFilter,
  onEnabledFilterChange,
  viewMode,
  onViewModeChange,
}: PoliciesToolbarProps) => {
  const controlOptions = controlGroups.map((cg) => ({
    label: cg.label,
    value: cg.key,
  }));

  return (
    <Form layout="inline" className="mb-6 flex grow gap-2">
      <Flex className="grow self-stretch">
        <Form.Item className="!me-0">
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
          value={enabledFilter}
          onChange={onEnabledFilterChange}
          className="min-w-[180px]"
          allowClear
        />
      </Form.Item>
      <Form.Item className="!me-0 self-end">
        <Select
          aria-label="Control"
          placeholder="Control"
          options={controlOptions}
          value={controlFilter}
          onChange={onControlFilterChange}
          className="!w-[240px]"
          allowClear
        />
      </Form.Item>
      <Form.Item className="!me-0 self-end">
        <Segmented
          value={viewMode}
          onChange={(value) => onViewModeChange(value as ViewMode)}
          options={[
            {
              label: <Icons.ShowDataCards size={16} />,
              value: "cards",
            },
            {
              label: <Icons.DataTable size={16} />,
              value: "table",
            },
          ]}
        />
      </Form.Item>
    </Form>
  );
};

export default PoliciesToolbar;
