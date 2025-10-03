import { AntMenu as Menu } from "fidesui";
import { useRouter } from "next/router";

import {
  NOTIFICATIONS_DIGESTS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";

const NotificationTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;

  // Determine which tab is active based on the current path
  const selectedKey = currentPath.startsWith(NOTIFICATIONS_DIGESTS_ROUTE)
    ? "digests"
    : "templates";

  const handleMenuClick = (key: string) => {
    if (key === "templates") {
      router.push(NOTIFICATIONS_TEMPLATES_ROUTE);
    } else if (key === "digests") {
      router.push(NOTIFICATIONS_DIGESTS_ROUTE);
    }
  };

  return (
    <Menu
      mode="horizontal"
      selectedKeys={[selectedKey]}
      onClick={({ key }) => handleMenuClick(key)}
      style={{ marginBottom: 24 }}
      items={[
        {
          key: "templates",
          label: "Templates",
        },
        {
          key: "digests",
          label: "Digests",
        },
      ]}
    />
  );
};

export default NotificationTabs;
