import { Button, forwardRef } from "@fidesui/react";
import React, { ReactElement } from "react";

interface NavButtonProps {
  disabled?: boolean;
  href?: string;
  isActive?: boolean;
  rightIcon?: ReactElement;
  title: string;
  onClick?: () => void;
}

export const NavButton = forwardRef(
  (
    { disabled, href, isActive, rightIcon, title, onClick }: NavButtonProps,
    ref
  ) => (
    <Button
      ref={ref}
      as="a"
      href={disabled ? undefined : href}
      onClick={onClick}
      variant="ghost"
      disabled={disabled}
      mr={4}
      colorScheme={isActive ? "complimentary" : "ghost"}
      rightIcon={rightIcon}
      data-testid={`nav-link-${title}`}
      isActive={isActive}
      _active={{ bg: "transparent" }}
    >
      {title}
    </Button>
  )
);

export default NavButton;
