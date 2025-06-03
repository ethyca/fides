import {
  ControlledSelect,
  ControlledSelectProps,
} from "~/features/common/form/ControlledSelect";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";

interface SharedConfigSelectProps
  extends Omit<ControlledSelectProps, "options"> {}

export const SharedConfigSelect = ({
  layout = "stacked",
  ...props
}: SharedConfigSelectProps) => {
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
    <ControlledSelect
      tooltip="If a shared monitor config is selected, the monitor will use the shared config to classify resources"
      options={sharedMonitorConfigOptions}
      label="Shared monitor config"
      layout={layout}
      {...props}
    />
  );
};
