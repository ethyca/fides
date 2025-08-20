import { AntMenuProps as MenuProps, Icons } from "fidesui";

export const COLLAPSE_BUTTON_TEXT = "show less";

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
