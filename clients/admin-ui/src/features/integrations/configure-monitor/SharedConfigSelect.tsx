import { ReactNode } from "react";

import {
  ControlledSelect,
  ControlledSelectProps,
} from "~/features/common/form/ControlledSelect";
import { CustomSelectOption } from "~/features/common/form/CustomSelectOption";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";

interface SharedConfigSelectProps
  extends Omit<ControlledSelectProps, "options"> {
  onManageClick: () => void;
}

const dropdownRender = (menu: ReactNode, onManageClick: () => void) => {
  return (
    <>
      <CustomSelectOption onClick={onManageClick}>
        View shared monitor configs
      </CustomSelectOption>
      {menu}
    </>
  );
};

export const SharedConfigSelect = ({
  onManageClick,
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
      {...props}
      tooltip="If a shared monitor config is selected, the monitor will use the shared config to classify resources"
      options={sharedMonitorConfigOptions}
      label="Shared monitor config"
      dropdownRender={(menu) => dropdownRender(menu, onManageClick)}
      layout={layout}
    />
  );
};
