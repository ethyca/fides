import { Drawer, DrawerProps } from "antd/lib";

const DRAWER_SIZE_MAP = {
  md: 480,
  lg: 720,
  xl: 992,
} as const;

type DrawerSize = keyof typeof DRAWER_SIZE_MAP;

export interface CustomDrawerProps extends Omit<DrawerProps, "width"> {
  /** Named size or explicit pixel/string width. Defaults to "md" (480px). */
  width?: DrawerSize | DrawerProps["width"];
}

/**
 * Higher-order Drawer with named size support and a sensible default width.
 *
 * Defaults:
 * - width: "md" (480px)
 */
export const CustomDrawer = ({
  width = "md",
  ...props
}: CustomDrawerProps) => {
  const resolvedWidth =
    typeof width === "string" && width in DRAWER_SIZE_MAP
      ? DRAWER_SIZE_MAP[width as DrawerSize]
      : width;

  return <Drawer width={resolvedWidth} {...props} />;
};
