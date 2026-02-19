import { Avatar, AvatarProps } from "antd/lib";
import classNames from "classnames";
import React from "react";

import styles from "./CustomAvatar.module.scss";

export interface CustomAvatarProps extends AvatarProps {
  /**
   * Visual style of the avatar.
   * - `filled`: solid background (Ant's default behaviour)
   * - `outlined`: transparent background with a 1px border using the Ant border token
   * @default "filled"
   */
  variant?: "outlined" | "filled";
}

/**
 * Higher-order component that adds an `outlined` variant to Ant Design's Avatar component.
 * The outlined variant renders a transparent badge with a 1px border, useful for icon
 * containers such as template icons and empty states.
 *
 * @example
 * // Filled (default — same as Ant Avatar)
 * <Avatar shape="circle" size={28} icon={<Icons.Checkmark />} style={{ backgroundColor: "var(--fidesui-success)" }} />
 *
 * @example
 * // Outlined square — e.g. document icon in an empty state
 * <Avatar shape="square" variant="outlined" size={64} icon={<Icons.Document size={32} />} />
 */
const withCustomProps = (WrappedComponent: typeof Avatar) => {
  const WrappedAvatar = React.forwardRef<HTMLSpanElement, CustomAvatarProps>(
    ({ variant = "filled", className, ...props }, ref) => {
      return (
        <WrappedComponent
          ref={ref}
          {...props}
          className={classNames(
            { [styles.outlined]: variant === "outlined" },
            className,
          )}
        />
      );
    },
  );

  WrappedAvatar.displayName = "CustomAvatar";
  return WrappedAvatar;
};

export const CustomAvatar = withCustomProps(Avatar);
