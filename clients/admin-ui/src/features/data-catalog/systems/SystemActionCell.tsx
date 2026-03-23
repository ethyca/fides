import { Button, Dropdown, Icons, MenuProps } from "fidesui";
import { useMemo } from "react";

interface SystemActionsCellProps {
  onDetailClick?: () => void;
}

const SystemActionsCell = ({ onDetailClick }: SystemActionsCellProps) => {
  const items: MenuProps["items"] = useMemo(() => {
    const menuItems: MenuProps["items"] = [];
    if (onDetailClick) {
      menuItems.push({
        key: "view-details",
        label: "View details",
        onClick: onDetailClick,
      });
    }
    return menuItems;
  }, [onDetailClick]);

  return (
    <Dropdown menu={{ items }}>
      <Button
        size="small"
        type="text"
        className="max-w-4"
        icon={<Icons.OverflowMenuVertical />}
        data-testid="system-actions-menu"
        aria-label="more"
      />
    </Dropdown>
  );
};

export default SystemActionsCell;
