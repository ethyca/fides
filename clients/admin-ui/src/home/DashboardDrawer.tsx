import { Drawer } from "fidesui";

import { AstralisDrawerContent } from "./AstralisDrawerContent";
import { PostureBreakdownContent } from "./PostureBreakdownContent";
import { closeDashboardDrawer, useDashboardDrawer } from "./useDashboardDrawer";

const DRAWER_CONFIG = {
  posture: { title: "Posture breakdown", content: PostureBreakdownContent },
  astralis: {
    title: "Astralis Agent Activity",
    content: AstralisDrawerContent,
  },
} as const;

export const DashboardDrawer = () => {
  const drawer = useDashboardDrawer();
  const config = drawer ? DRAWER_CONFIG[drawer.type] : null;

  return (
    <Drawer
      open={drawer !== null}
      onClose={closeDashboardDrawer}
      placement="right"
      width={480}
      title={config?.title}
      destroyOnClose
    >
      {config && <config.content />}
    </Drawer>
  );
};
