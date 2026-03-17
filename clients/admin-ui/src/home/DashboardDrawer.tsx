import { Drawer } from "fidesui";

import { PostureBreakdownContent } from "./PostureBreakdownContent";
import { closeDashboardDrawer, useDashboardDrawer } from "./useDashboardDrawer";

const DrawerContent = ({ type }: { type: string }) => {
  switch (type) {
    case "posture":
      return <PostureBreakdownContent />;
    default:
      return null;
  }
};

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
      {drawer && <DrawerContent type={drawer.type} />}
    </Drawer>
  );
};
