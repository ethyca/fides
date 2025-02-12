import { ComponentChildren, h, VNode } from "preact";

import { useDisclosure } from "../lib/hooks";
import Toggle from "./Toggle";

const DataUseToggle = ({
  noticeKey,
  title,
  checked,
  onToggle,
  children,
  badge,
  gpcBadge,
  disabled,
  onLabel,
  offLabel,
  isHeader,
  includeToggle = true,
}: {
  noticeKey: string;
  title: string;
  checked: boolean;
  onToggle: (noticeKey: string) => void;
  children?: ComponentChildren;
  badge?: string;
  gpcBadge?: VNode;
  disabled?: boolean;
  onLabel?: string;
  offLabel?: string;
  isHeader?: boolean;
  includeToggle?: boolean;
}) => {
  const {
    isOpen,
    getButtonProps,
    getDisclosureProps,
    onToggle: toggleDescription,
  } = useDisclosure({ id: noticeKey });

  const handleKeyDown = (event: KeyboardEvent, isClickable: boolean) => {
    if (event.code === "Space" || event.code === "Enter") {
      event.preventDefault();
      if (isClickable) {
        toggleDescription();
      }
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
      <div key={noticeKey} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={(e) => handleKeyDown(e, isClickable)}
          {...buttonProps}
          className={
            isHeader
              ? "fides-notice-toggle-trigger fides-notice-toggle-header"
              : "fides-notice-toggle-trigger"
          }
        >
          <span className="fides-flex-center fides-justify-space-between">
            {title}
          </span>
        </span>
        <span className="fides-notice-toggle-controls">
          {gpcBadge}
          {badge ? <span className="fides-notice-badge">{badge}</span> : null}
          {includeToggle ? (
            <Toggle
              label={title}
              name={noticeKey}
              id={noticeKey}
              checked={checked}
              onChange={onToggle}
              disabled={disabled}
              onLabel={onLabel}
              offLabel={offLabel}
            />
          ) : null}
        </span>
      </div>
      {children ? <div {...getDisclosureProps()}>{children}</div> : null}
    </div>
  );
};

export default DataUseToggle;
