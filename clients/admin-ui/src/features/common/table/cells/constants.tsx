import { AntMenuProps as MenuProps, Icons } from "fidesui";

export const COLLAPSE_BUTTON_TEXT = "show less";

/**
 * Import this to use the expand/collapse all menu items in table columns.
 * @example
 * const columns = [{
 *   title: "My Column",
 *   menu: {
 *     items: expandCollapseAllMenuItems,
 *     onClick: (e) => {
 *       if (e.key === "expand-all") {
 *         setIsMyColumnExpanded(true);
 *       } else if (e.key === "collapse-all") {
 *         setIsMyColumnExpanded(false);
 *       } else if (e.key === "custom-item") {
 *         // Do something
 *       }
 *     },
 *   }
 * }];
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
