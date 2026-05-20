import { Button, ButtonProps } from "antd/lib";
import React from "react";

export interface CustomButtonProps extends ButtonProps {
  /**
   * Whether the button renders with rounded corners. When `false`, the button
   * is rendered with squared corners (border-radius: 0). Defaults to `true` so
   * the theme's default radius is preserved.
   */
  rounded?: boolean;
}

export const CustomButton = React.forwardRef<HTMLButtonElement, CustomButtonProps>(
  ({ rounded = true, style, ...props }, ref) => (
    <Button
      ref={ref}
      style={rounded ? style : { borderRadius: 0, ...style }}
      {...props}
    />
  ),
);

CustomButton.displayName = "CustomButton";
