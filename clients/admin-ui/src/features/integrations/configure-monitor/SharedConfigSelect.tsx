import { Form, FormItemProps, Select, SelectProps } from "fidesui";

import {} from "~/features/common/form/ControlledSelect";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";

interface SharedConfigSelectProps extends Omit<SelectProps, "options"> {}

export const SharedConfigSelect = ({
  itemProps,
  selectProps,
}: {
  selectProps: SharedConfigSelectProps;
  itemProps: FormItemProps;
}) => {
  const { data: sharedMonitorConfigs } = useGetSharedMonitorConfigsQuery({
    page: 1,
    size: 100,
  });

  const sharedMonitorConfigOptions = sharedMonitorConfigs?.items.map(
    (config) => ({
      label: config.name,
      value: config.id,
    }),
  );

  return (
    <Form.Item
      label="Shared monitor config"
      data-testid="controlled-select-shared_config_id"
      {...itemProps}
    >
      <Select options={sharedMonitorConfigOptions} {...selectProps} />
    </Form.Item>
  );
};
