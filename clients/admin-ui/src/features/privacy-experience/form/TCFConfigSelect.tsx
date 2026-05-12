import { Form, Select } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectTCFConfigFilters,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf/tcf-config.slice";

const getTcfTooltip = (
  overridesEnabled: boolean,
  hasOptions: boolean,
): string => {
  if (!overridesEnabled) {
    return "You must enable the Override vendor purposes setting in consent settings to select a TCF configuration.";
  }
  if (!hasOptions) {
    return "No TCF configurations found. Please create a TCF configuration in 'Consent settings' to select one.";
  }
  return 'Select a TCF configuration. Configurations are defined in "Consent settings" and apply to TCF privacy experiences.';
};

export const TCFConfigSelect = ({
  overridesEnabled,
}: {
  overridesEnabled: boolean;
}) => {
  const tcfConfigFilters = useAppSelector(selectTCFConfigFilters);
  const { data: tcfConfigs } = useGetTCFConfigurationsQuery(tcfConfigFilters);

  const tcfConfigOptions = useMemo(
    () =>
      tcfConfigs?.items.map((config) => ({
        label: config.name,
        value: config.id,
      })) ?? [],
    [tcfConfigs],
  );

  return (
    <Form.Item
      name="tcf_configuration_id"
      label="TCF Configuration"
      tooltip={getTcfTooltip(overridesEnabled, !!tcfConfigOptions?.length)}
    >
      <Select
        options={tcfConfigOptions}
        disabled={!tcfConfigOptions?.length || !overridesEnabled}
        allowClear
        id="tcf_configuration_id"
        aria-label="TCF Configuration"
        data-testid="controlled-select-tcf_configuration_id"
      />
    </Form.Item>
  );
};
