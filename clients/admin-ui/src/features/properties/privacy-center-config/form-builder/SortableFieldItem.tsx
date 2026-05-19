import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Icons } from "fidesui";
import React from "react";

interface SortableFieldItemProps {
  id: string;
  selected?: boolean;
  onSelect: (id: string) => void;
  children: React.ReactNode;
}

const containerStyle = (selected: boolean): React.CSSProperties => ({
  display: "flex",
  alignItems: "flex-start",
  gap: 4,
  padding: "4px 8px 8px 4px",
  marginBottom: 4,
  borderRadius: 4,
  border: selected
    ? "1px solid var(--fidesui-color-primary)"
    : "1px solid transparent",
  background: selected ? "var(--fidesui-color-primary-bg)" : "transparent",
  cursor: "pointer",
});

const handleStyle: React.CSSProperties = {
  cursor: "grab",
  display: "flex",
  alignItems: "center",
  touchAction: "none",
};

export const SortableFieldItem = ({
  id,
  selected = false,
  onSelect,
  children,
}: SortableFieldItemProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style: React.CSSProperties = {
    ...containerStyle(selected),
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    /* eslint-disable jsx-a11y/no-noninteractive-element-interactions, jsx-a11y/no-noninteractive-tabindex -- listitem with click/keyboard handlers is intentional for field selection */
    <div
      ref={setNodeRef}
      style={style}
      // Edit-mode chrome: zero out Form.Item margin since the card itself
      // provides the vertical rhythm. Preview mode renders without this
      // wrapper so fields keep their natural form-item spacing.
      className="[&_.ant-form-item]:!mb-0"
      data-element-id={id}
      data-testid={`sortable-field-${id}`}
      role="listitem"
      tabIndex={0}
      onClick={(e) => {
        e.stopPropagation();
        if (!isDragging) {
          onSelect(id);
        }
      }}
      // Auto-select on focus so keyboard users (Tab) populate the
      // properties panel without an extra Space/Enter press. The
      // onKeyDown handler still satisfies activation for AT users
      // who expect a button to be pressable.
      onFocus={() => {
        if (!isDragging) {
          onSelect(id);
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(id);
        }
      }}
    >
      <span
        style={handleStyle}
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...attributes}
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...listeners}
        aria-label={`Drag handle for ${id}`}
        data-testid={`drag-handle-${id}`}
      >
        <Icons.Draggable size={20} color="var(--fidesui-neutral-400)" />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
    </div>
    /* eslint-enable jsx-a11y/no-noninteractive-element-interactions, jsx-a11y/no-noninteractive-tabindex */
  );
};
