import { AntMenu as Menu } from "fidesui";
import { useRouter } from "next/router";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  MESSAGING_PROVIDERS_ROUTE,
  NOTIFICATIONS_DIGESTS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";
import { ScopeRegistryEnum } from "~/types/api";

import { selectThisUsersScopes } from "../user-management";

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
      requiresPlus: true,
      scopes: [ScopeRegistryEnum.MESSAGING_TEMPLATE_UPDATE],
    },
    {
      key: "digests",
      label: "Digests",
      requiresPlus: true,
      scopes: [ScopeRegistryEnum.DIGEST_CONFIG_READ],
    },
    {
      key: "providers",
      label: "Providers",
      requiresPlus: false,
      scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
    },
  ];

  // Remove unavailable tabs if not running plus
  if (!plus) {
    menuItems = menuItems.filter((item) => item.requiresPlus);
  }

  // Filter scopes
  const userScopes = useAppSelector(selectThisUsersScopes);
  menuItems = menuItems.filter((item) =>
    item.scopes.some((scope) => userScopes.includes(scope)),
  );

  return (
    <div className="mb-6">
      <Menu
        mode="horizontal"
        selectedKeys={[selectedKey]}
        onClick={({ key }) => handleMenuClick(key)}
        items={menuItems}
      />
    </div>
  );
};

export default NotificationTabs;
