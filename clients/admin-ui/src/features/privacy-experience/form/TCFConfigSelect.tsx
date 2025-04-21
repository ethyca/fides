import { AntTooltip as Tooltip } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import {
  selectTCFConfigFilters,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf/tcf-config.slice";

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
    <Tooltip
      title={
        // eslint-disable-next-line no-nested-ternary
        !overridesEnabled
          ? "You must enable the Override vendor purposes setting in consent settings to select a TCF configuration."
          : !tcfConfigOptions?.length
            ? "No TCF configurations found. Please create a TCF configuration in 'Consent settings' to select one."
            : undefined
      }
    >
      <div>
        <ControlledSelect
          name="tcf_configuration_id"
          id="tcf_configuration_id"
          label="TCF Configuration"
          options={tcfConfigOptions}
          layout="stacked"
          disabled={!tcfConfigOptions?.length || !overridesEnabled}
          tooltip='Select a TCF configuration. Configurations are defined in "Consent settings" and apply to TCF privacy experiences.'
          allowClear
        />
      </div>
    </Tooltip>
  );
};
