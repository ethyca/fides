import { Drawer, DrawerProps } from "antd/lib";

const DEFAULT_WIDTH = 480;

/**
 * Wrapper around Ant Drawer that sets the default width to 480px.
 */
export const CustomDrawer = ({ width, size, ...props }: DrawerProps) => {
  return (
    <Drawer
      width={size ? undefined : (width ?? DEFAULT_WIDTH)}
      size={size}
      {...props}
    />
  );
};
