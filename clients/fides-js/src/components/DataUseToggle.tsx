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
}: {
  dataUse: DataUse;
  checked: boolean;
  onToggle: (noticeKey: DataUse["key"]) => void;
  children: ComponentChildren;
  badge?: string;
  gpcBadge?: VNode;
  disabled?: boolean;
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

  return (
    <div
      className={
        isOpen
          ? "fides-notice-toggle fides-notice-toggle-expanded"
          : "fides-notice-toggle"
      }
    >
      <div key={dataUse.key} className="fides-notice-toggle-title">
        <span
          role="button"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          {...getButtonProps()}
          className="fides-notice-toggle-trigger"
        >
          <span className="fides-flex-center">
            {dataUse.name}
            {badge ? <span className="fides-notice-badge">{badge}</span> : null}
          </span>
          {gpcBadge}
        </span>

        <Toggle
          name={dataUse.name || ""}
          id={dataUse.key}
          checked={checked}
          onChange={onToggle}
          disabled={disabled}
        />
      </div>
      <div {...getDisclosureProps()}>{children}</div>
    </div>
  );
};

export default DataUseToggle;
