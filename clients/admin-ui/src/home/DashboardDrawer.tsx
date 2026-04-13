import { antTheme, Drawer } from "fidesui";

import { PostureBreakdownContent } from "./PostureBreakdownContent";
import { closeDashboardDrawer, useDashboardDrawer } from "./useDashboardDrawer";

const DRAWER_CONFIG = {
  posture: {
    title: "Governance Posture Score",
    content: PostureBreakdownContent,
  },
} as const;

export const DashboardDrawer = () => {
  const drawer = useDashboardDrawer();
  const config = drawer ? DRAWER_CONFIG[drawer.type] : null;
  const { token } = antTheme.useToken();

  return (
    <Drawer
      open={drawer !== null}
      onClose={closeDashboardDrawer}
      placement="right"
      width={480}
      title={config?.title}
      destroyOnClose
      styles={{
        header: { background: token.colorBgContainer, borderBottom: "none" },
        body: { background: token.colorBgContainer },
      }}
    >
      {config && <config.content />}
    </Drawer>
  );
};
