import { Flex, Select, SelectProps } from "fidesui";
import { MouseEventHandler, ReactNode } from "react";

import { CustomSelectOption } from "~/features/common/form/CustomSelectOption";

import { MOCK_SYSTEM_SELECT_OPTIONS } from "../mock/mockCloudInfraSystems";
import { SystemLeadingIcon } from "./SystemLeadingIcon";

const SystemLabel = ({
  value,
  label,
}: {
  value?: string | number | null;
  label?: ReactNode;
}) => (
  <Flex align="center" gap="small" className="overflow-hidden">
    <SystemLeadingIcon value={value} />
    <span className="overflow-hidden text-ellipsis">{label}</span>
  </Flex>
);

// Stable module-scope renderers (passed to optionRender/labelRender) so React
// doesn't tear down the subtree on every parent render.
const renderSystemOption = (option: {
  value?: string | number | null;
  label?: ReactNode;
}) => <SystemLabel value={option.value} label={option.label} />;

const renderSystemSelectedLabel = (labelInValue: {
  value?: string | number;
  label?: ReactNode;
}) => <SystemLabel value={labelInValue.value} label={labelInValue.label} />;

const popupRender = (
  menu: ReactNode,
  onAddSystem: MouseEventHandler<HTMLElement>,
) => (
  <>
    <CustomSelectOption
      onClick={onAddSystem}
      data-testid="add-new-system"
      id="add-new-system"
    >
      Add new system +
    </CustomSelectOption>
    {menu}
  </>
);

interface MockSystemSelectProps extends Omit<SelectProps, "options"> {
  onAddSystem?: MouseEventHandler<HTMLButtonElement>;
}

/**
 * Drop-in replacement for SystemSelect in the AWS cloud-infra prototype. Lists
 * the mock AWS / business-application catalog (grouped) and renders each
 * system's logo in both the dropdown and the selected tags. Option labels stay
 * plain strings so the stored selection renders cleanly elsewhere (tree, tags).
 */
export const MockSystemSelect = ({
  onAddSystem,
  ...props
}: MockSystemSelectProps) => (
  <Select
    placeholder="Search systems..."
    aria-label="Search for a system to select"
    showSearch
    optionFilterProp="label"
    data-testid="system-select"
    options={MOCK_SYSTEM_SELECT_OPTIONS}
    optionRender={renderSystemOption}
    labelRender={renderSystemSelectedLabel}
    popupRender={
      onAddSystem ? (menu) => popupRender(menu, onAddSystem) : undefined
    }
    {...props}
  />
);
