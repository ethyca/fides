import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntDropdownProps as DropdownProps,
  AntFlex as Flex,
  AntMenuProps as MenuProps,
  Icons,
} from "fidesui";
import { ReactNode } from "react";

/**
 * Import this to use the expand/collapse all menu items in the MenuHeaderCell.
 * @example
 * <MenuHeaderCell
 *   title="My Column"
 *   menu={{
 *     items: [...expandCollapseAllMenuItems, {
 *       key: "custom-item",
 *       label: "Custom item",
 *       icon: <Icons.CustomIcon />,
 *     }],
 *     onClick: (e) => {
 *       if (e.key === "expand-all") {
 *         setIsMyColumnExpanded(true);
 *       } else if (e.key === "collapse-all") {
 *         setIsMyColumnExpanded(false);
 *       } else if (e.key === "custom-item") {
 *         // Do something
 *       }
 *     },
 *   }}
 */
export const expandCollapseAllMenuItems: MenuProps["items"] = [
  {
    key: "expand-all",
    label: "Expand all",
    icon: <Icons.ExpandAll />,
  },
  {
    key: "collapse-all",
    label: "Collapse all",
    icon: <Icons.CollapseAll />,
  },
];

interface MenuHeaderCellProps extends DropdownProps {
  title: string;
  menuIcon?: ReactNode;
  menuIconLabel?: string;
  menu?: MenuProps;
}

/**
 * A header cell that displays a title and a menu button.
 * @param title - The title of the header cell.
 * @param menuIcon - The icon to display in the menu.
 * @param menuIconLabel - The a11y label for the menu icon.
 * @param menu - The menu to display (extends AntDropdownProps).
 */
export const MenuHeaderCell = ({
  title,
  menuIcon,
  menuIconLabel = "Menu",
  menu,
  ...dropdownProps
}: MenuHeaderCellProps) => {
  return (
    <Flex align="center" justify="space-between">
      {title}
      <Dropdown
        trigger={["click"]}
        menu={menu}
        placement="bottomRight"
        {...dropdownProps}
      >
        <Button
          icon={
            menuIcon || <Icons.OverflowMenuVertical title={menuIconLabel} />
          }
          size="small"
          type="text"
          // Use the filter button class name to match other button styles in the table header
          // eslint-disable-next-line tailwindcss/no-custom-classname
          className="ant-table-filter-trigger"
        />
      </Dropdown>
    </Flex>
  );
};
