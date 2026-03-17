import { Button, Dropdown, Icons, MenuProps } from "fidesui";
import { useMemo } from "react";

const CatalogResourceOverflowMenu = ({
  onHideClick,
  onDetailClick,
}: {
  onHideClick?: () => void;
  onDetailClick?: () => void;
}) => {
  const items: MenuProps["items"] = useMemo(() => {
    const menuItems: MenuProps["items"] = [];
    if (onDetailClick) {
      menuItems.push({
        key: "view-details",
        label: "View details",
        onClick: onDetailClick,
      });
    }
    if (onHideClick) {
      menuItems.push({
        key: "hide",
        label: "Hide",
        onClick: onHideClick,
      });
    }
    return menuItems;
  }, [onDetailClick, onHideClick]);

  return (
    <Dropdown menu={{ items }}>
      <Button
        size="small"
        type="text"
        icon={<Icons.OverflowMenuVertical />}
        className="w-6 gap-0"
        data-testid="actions-menu"
        aria-label="more"
      />
    </Dropdown>
  );
};

export default CatalogResourceOverflowMenu;
