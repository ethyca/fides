import { Menu } from "fidesui";
import { useRouter } from "next/router";

import type { NavConfigTab } from "~/features/common/nav/nav-config";
import {
  ACCESS_CONTROL_REQUEST_LOG_ROUTE,
  ACCESS_CONTROL_SUMMARY_ROUTE,
} from "~/features/common/nav/routes";

/** Shared tab definitions used by both the tab bar and nav search. */
export const ACCESS_CONTROL_TAB_ITEMS: NavConfigTab[] = [
  { title: "Summary", path: ACCESS_CONTROL_SUMMARY_ROUTE },
  { title: "Request log", path: ACCESS_CONTROL_REQUEST_LOG_ROUTE },
];

const AccessControlTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;

  let selectedKey = "summary";
  if (currentPath.startsWith(ACCESS_CONTROL_REQUEST_LOG_ROUTE)) {
    selectedKey = "request-log";
  } else if (currentPath.startsWith(ACCESS_CONTROL_SUMMARY_ROUTE)) {
    selectedKey = "summary";
  }

  const menuItems = ACCESS_CONTROL_TAB_ITEMS.map((tab) => ({
    key: tab.path === ACCESS_CONTROL_SUMMARY_ROUTE ? "summary" : "request-log",
    label: tab.title,
    path: tab.path,
  }));

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

export default AccessControlTabs;
