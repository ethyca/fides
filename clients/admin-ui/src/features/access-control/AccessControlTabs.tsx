import { Menu } from "fidesui";
import { useRouter } from "next/router";

import {
  ACCESS_CONTROL_REQUEST_LOG_ROUTE,
  ACCESS_CONTROL_SUMMARY_ROUTE,
} from "~/features/common/nav/routes";

export const AccessControlTabs = () => {
  const router = useRouter();
  const currentPath = router.pathname;

  let selectedKey = "summary";
  if (currentPath.startsWith(ACCESS_CONTROL_REQUEST_LOG_ROUTE)) {
    selectedKey = "request-log";
  } else if (currentPath.startsWith(ACCESS_CONTROL_SUMMARY_ROUTE)) {
    selectedKey = "summary";
  }

  const menuItems = [
    {
      key: "summary",
      label: "Summary",
      path: ACCESS_CONTROL_SUMMARY_ROUTE,
    },
    {
      key: "request-log",
      label: "Request log",
      path: ACCESS_CONTROL_REQUEST_LOG_ROUTE,
    },
  ];

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
