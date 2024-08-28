import { FunctionComponent, h } from "preact";
import { JSXInternal } from "preact/src/jsx";

interface MenuItemProps extends JSXInternal.HTMLAttributes<HTMLButtonElement> {
  isActive: boolean;
}

const MenuItem: FunctionComponent<MenuItemProps> = ({
  isActive,
  className,
  children,
  ...props
}) => (
  <button
    type="button"
    aria-pressed={isActive || undefined}
    {...props}
    className={`fides-banner-button fides-menu-item ${className || ""}`}
  >
    {children}
  </button>
);

export default MenuItem;
