import { AntButton as Button, AntButtonProps } from "fidesui";

interface CustomSelectOptionProps extends Omit<AntButtonProps, "type"> {}

/**
 * A button that looks like an Ant Select Option for use in custom dropdowns.
 * NOTE: Use with caution, as this option will not be keyboard accessible. Ideally use the Ant Select component's native menu or have a fallback for keyboard users.
 * @params extend AntButton
 */
export const CustomSelectOption = ({
  children,
  className,
  style,
  ...props
}: CustomSelectOptionProps) => {
  return (
    <Button
      {...props}
      type="text"
      className={`w-full justify-start ${className}`}
      style={{
        fontWeight: 600,
        padding: "var(--ant-select-option-padding)",
        backgroundColor: "var(--ant-select-option-selected-bg)",
        ...style,
      }}
    >
      {children}
    </Button>
  );
};
