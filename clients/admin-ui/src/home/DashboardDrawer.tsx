import { Drawer } from "fidesui";

import { closeDashboardDrawer, useDashboardDrawer } from "./useDashboardDrawer";

export const DashboardDrawer = () => {
  const drawer = useDashboardDrawer();

  return (
    <Drawer
      open={drawer !== null}
      onClose={closeDashboardDrawer}
      placement="right"
      width={drawer?.width ?? 480}
      title={drawer?.title}
      destroyOnClose
    >
      {drawer?.content}
    </Drawer>
  );
};
