import {
  AntFormItemProps as FormItemProps,
  AntSelect as Select,
} from "fidesui";
import { ComponentProps } from "react";

import { FormikSelect } from "~/features/common/form/FormikSelect";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";

type SharedConfigSelectProps = ComponentProps<typeof Select> &
  Pick<
    FormItemProps,
    "required" | "name" | "label" | "tooltip" | "help" | "extra"
  > & {
    error?: string;
    touched?: boolean;
  };

export const FormikSharedConfigSelect = (props: SharedConfigSelectProps) => {
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
    <FormikSelect
      tooltip="If a shared monitor config is selected, the monitor will use the shared config to classify resources"
      options={sharedMonitorConfigOptions}
      label="Shared monitor config"
      {...props}
    />
  );
};
