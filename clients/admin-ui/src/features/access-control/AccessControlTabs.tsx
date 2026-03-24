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

  let selectedKey = ACCESS_CONTROL_SUMMARY_ROUTE;
  if (currentPath.startsWith(ACCESS_CONTROL_REQUEST_LOG_ROUTE)) {
    selectedKey = ACCESS_CONTROL_REQUEST_LOG_ROUTE;
  }

  const items = ACCESS_CONTROL_TAB_ITEMS.map((tab) => ({
    key: tab.path,
    label: tab.title,
  }));

  return (
    <div className="mb-6">
      <Menu
        mode="horizontal"
        selectedKeys={[selectedKey]}
        onClick={({ key }) => router.push(key)}
        items={items}
      />
    </div>
  );
};

export default AccessControlTabs;
