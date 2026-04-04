import { Form, Icons, Select, Tooltip } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
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
    <div>
      <Form.Item
        name="tcf_configuration_id"
        label="TCF Configuration"
        tooltip={{
          title:
            'Select a TCF configuration. Configurations are defined in "Consent settings" and apply to TCF privacy experiences.',
          icon: <Icons.InformationFilled color="var(--fidesui-neutral-200)" />,
        }}
      >
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
          {/* span helps tooltip work when select is disabled */}
          <span>
            <Select
              options={tcfConfigOptions}
              disabled={!tcfConfigOptions?.length || !overridesEnabled}
              allowClear
              id="tcf_configuration_id"
              aria-label="TCF Configuration"
              data-testid="controlled-select-tcf_configuration_id"
            />
          </span>
        </Tooltip>
      </Form.Item>
    </div>
  );
};
