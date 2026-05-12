import { Drawer, type DrawerProps } from "antd/lib";

export type { DrawerProps } from "antd/lib";

const DEFAULT_WIDTH = 480;

/**
 * Wrapper around Ant Drawer that sets the default width to 480px.
 *
 * In antd v6, `width` is deprecated in favor of `size`, which accepts both
 * the enum values (`"default"` / `"large"`) and numeric/string pixel widths.
 * We forward the deprecated `width` prop into `size` for backward compatibility
 * with existing call sites.
 */
export const CustomDrawer = ({ width, size, ...props }: DrawerProps) => {
  return <Drawer size={size ?? width ?? DEFAULT_WIDTH} {...props} />;
};
