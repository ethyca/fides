import { ComponentChildren, VNode, h } from "preact";
import { useDisclosure } from "../lib/hooks";
import Toggle from "./Toggle";

interface DataUse {
  key: string;
  name?: string;
}

const DataUseToggle = ({
  dataUse,
  checked,
  onToggle,
  children,
  badge,
  gpcBadge,
  disabled,
  isHeader,
  includeToggle = true,
}: {
  dataUse: DataUse;
  checked: boolean;
  onToggle: (noticeKey: DataUse["key"]) => void;
  children?: ComponentChildren;
  badge?: string;
  gpcBadge?: VNode;
  disabled?: boolean;
  isHeader?: boolean;
  includeToggle?: boolean;
}) => {
  const {
    isOpen,
    getButtonProps,
    getDisclosureProps,
    onToggle: toggleDescription,
  } = useDisclosure({
    id: dataUse.key,
  });

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === "Space" || event.code === "Enter") {
      toggleDescription();
    }
  };

  const isClickable = children != null;
  const buttonProps = isClickable ? getButtonProps() : {};

  return (
    <div
      className={
        isOpen && isClickable
          ? "fides-notice-toggle fides-notice-toggle-expanded"
          : "fides-notice-toggle"
      }
    >
      <div key={dataUse.key} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={isClickable ? handleKeyDown : undefined}
          {...buttonProps}
          className={
            isHeader
              ? "fides-notice-toggle-trigger fides-notice-toggle-header"
              : "fides-notice-toggle-trigger"
          }
        >
          <span className="fides-flex-center fides-justify-space-between">
            {dataUse.name}
            {badge ? <span className="fides-notice-badge">{badge}</span> : null}
          </span>
          {gpcBadge}
        </span>
        {includeToggle ? (
          <Toggle
            name={dataUse.name || ""}
            id={dataUse.key}
            checked={checked}
            onChange={onToggle}
            disabled={disabled}
          />
        ) : null}
      </div>
      {children ? <div {...getDisclosureProps()}>{children}</div> : null}
    </div>
  );
};

export default DataUseToggle;
