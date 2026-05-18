import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Flex, Icons, Switch } from "fidesui";
import React from "react";

type DraggableColumnListItemProps = {
  id: string;
  isVisible: boolean;
  text: string;
  setColumnVisible: (id: string, isVisible: boolean) => void;
};

export const DraggableColumnListItem = ({
  id,
  isVisible,
  setColumnVisible,
  text,
}: DraggableColumnListItemProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.2 : 1,
  };

  const handleColumnVisibleToggle = (checked: boolean) => {
    setColumnVisible(id, checked);
  };

  return (
    <Flex
      align="center"
      ref={setNodeRef}
      style={style}
      data-testid={`column-list-item-${id}`}
      gap="small"
      className="py-1" // use padding instead of parent flex gap to better support dragging
    >
      <div
        {...attributes}
        {...listeners}
        style={{
          cursor: isDragging ? "grabbing" : "grab",
          touchAction: "none",
        }}
        className="-ml-1 shrink-0"
        data-testid={`column-dragger-${id}`}
      >
        <Icons.Draggable size={20} color="var(--fidesui-neutral-400)" />
      </div>
      <Flex align="center" className="min-w-0 flex-1" title={text}>
        <label htmlFor={id} className="mb-0 min-w-0 flex-1 truncate text-sm">
          {text}
        </label>
        <Switch
          id={id}
          size="small"
          checked={isVisible}
          onChange={handleColumnVisibleToggle}
        />
      </Flex>
    </Flex>
  );
};
