import { Menu } from "fidesui";
import { useRouter } from "next/router";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  CHAT_PROVIDERS_ROUTE,
  MESSAGING_PROVIDERS_ROUTE,
  NOTIFICATIONS_DIGESTS_ROUTE,
  NOTIFICATIONS_TEMPLATES_ROUTE,
} from "~/features/common/nav/routes";
import { ScopeRegistryEnum } from "~/types/api";

import { selectThisUsersScopes } from "../user-management";

const NotificationTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;
  const { plus, flags } = useFeatures();

  // Determine which tab is active based on the current path
  let selectedKey = "email-providers"; // Default to email providers for non-Plus
  if (currentPath.startsWith(MESSAGING_PROVIDERS_ROUTE)) {
    selectedKey = "email-providers";
  } else if (currentPath.startsWith(CHAT_PROVIDERS_ROUTE)) {
    selectedKey = "chat-providers";
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
      key: "email-providers",
      label: "Email providers",
      requiresPlus: false,
      scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      path: MESSAGING_PROVIDERS_ROUTE,
    },
    {
      key: "chat-providers",
      label: "Chat providers",
      requiresPlus: true,
      requiresFlag: "alphaDataProtectionAssessments" as const,
      scopes: [ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE],
      path: CHAT_PROVIDERS_ROUTE,
    },
  ];

  // Remove unavailable tabs if not running plus
  if (!plus) {
    menuItems = menuItems.filter((item) => !item.requiresPlus);
  }

  // Remove tabs that require a feature flag that isn't enabled
  menuItems = menuItems.filter(
    (item) =>
      !("requiresFlag" in item) ||
      (item.requiresFlag === "alphaDataProtectionAssessments" &&
        flags?.alphaDataProtectionAssessments),
  );

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
