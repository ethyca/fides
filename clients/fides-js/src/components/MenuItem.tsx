import { h, FunctionComponent } from "preact";
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
    className={`fides-banner-button fides-menu-item ${className}`}
    id={isActive ? "fides-menu-item-active" : ""}
    aria-pressed={isActive || undefined}
    {...props}
  >
    {children}
  </button>
);

export default MenuItem;
