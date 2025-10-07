import { AntMenu as Menu } from "fidesui";
import { useRouter } from "next/router";

import {
  MESSAGING_PROVIDERS_ROUTE,
  NOTIFICATIONS_DIGESTS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";

const NotificationTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;

  // Determine which tab is active based on the current path
  let selectedKey = "templates";
  if (currentPath.startsWith(MESSAGING_PROVIDERS_ROUTE)) {
    selectedKey = "providers";
  } else if (currentPath.startsWith(NOTIFICATIONS_DIGESTS_ROUTE)) {
    selectedKey = "digests";
  }

  const handleMenuClick = (key: string) => {
    if (key === "templates") {
      router.push(NOTIFICATIONS_TEMPLATES_ROUTE);
    } else if (key === "digests") {
      router.push(NOTIFICATIONS_DIGESTS_ROUTE);
    } else if (key === "providers") {
      router.push(MESSAGING_PROVIDERS_ROUTE);
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
        {
          key: "providers",
          label: "Providers",
        },
      ]}
    />
  );
};

export default NotificationTabs;
