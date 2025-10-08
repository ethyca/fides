import { AntMenu as Menu } from "fidesui";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import {
  MESSAGING_PROVIDERS_ROUTE,
  NOTIFICATIONS_DIGESTS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";

const NotificationTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;
  const { plus } = useFeatures();

  // Determine which tab is active based on the current path
  let selectedKey = "providers"; // Default to digests for non-Plus
  if (currentPath.startsWith(MESSAGING_PROVIDERS_ROUTE)) {
    selectedKey = "providers";
  } else if (currentPath.startsWith(NOTIFICATIONS_TEMPLATES_ROUTE)) {
    selectedKey = "templates";
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

  let menuItems = [
    {
      key: "templates",
      label: "Templates",
      requiredPlus: true,
    },
    {
      key: "digests",
      label: "Digests",
      requiredPlus: true,
    },
    {
      key: "providers",
      label: "Providers",
      requiredPlus: false,
    },
  ];

  // Remove unavailable tabs if not running plus
  if (!plus) {
    menuItems = menuItems.filter((item) => item.requiredPlus);
  }

  return (
    <Menu
      mode="horizontal"
      selectedKeys={[selectedKey]}
      onClick={({ key }) => handleMenuClick(key)}
      style={{ marginBottom: 24 }}
      items={menuItems}
    />
  );
};

export default NotificationTabs;
