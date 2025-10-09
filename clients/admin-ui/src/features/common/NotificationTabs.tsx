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

  let menuItems = [
    {
      key: "templates",
      label: "Templates",
      requiresPlus: true,
      scopes: [ScopeRegistryEnum.MESSAGING_TEMPLATE_UPDATE],
      path: NOTIFICATIONS_TEMPLATES_ROUTE,
    },
    {
      key: "digests",
      label: "Digests",
      requiresPlus: true,
      scopes: [ScopeRegistryEnum.DIGEST_CONFIG_READ],
      path: NOTIFICATIONS_DIGESTS_ROUTE,
    },
    {
      key: "providers",
      label: "Providers",
      requiresPlus: false,
      scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      path: MESSAGING_PROVIDERS_ROUTE,
    },
  ];

  // Remove unavailable tabs if not running plus
  if (!plus) {
    menuItems = menuItems.filter((item) => !item.requiresPlus);
  }

  // Filter scopes
  const userScopes = useAppSelector(selectThisUsersScopes);
  menuItems = menuItems.filter((item) =>
    item.scopes.some((scope) => userScopes.includes(scope)),
  );

  const handleMenuClick = (key: string) => {
    const item = menuItems.find((i) => i.key === key);
    if (item) {
      router.push(item.path);
    }
  };

  const items = menuItems.map((item) => ({
    label: item.label,
    key: item.key,
    path: item.path,
  }));

  return (
    <div className="mb-6">
      <Menu
        mode="horizontal"
        selectedKeys={[selectedKey]}
        onClick={({ key }) => handleMenuClick(key)}
        items={items}
      />
    </div>
  );
};

export default NotificationTabs;
