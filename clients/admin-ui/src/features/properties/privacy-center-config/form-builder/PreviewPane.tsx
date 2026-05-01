import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { JSONUIProvider, Renderer } from "@json-render/react";
import { Button, Dropdown, Empty, Form } from "fidesui";
import React from "react";

import type { ComponentType } from "./catalog";
import { catalog } from "./catalog";
import type { JsonRenderSpec } from "./mapper";
import { registry } from "./registry";
import { SortableFieldItem } from "./SortableFieldItem";

type EditableComponentType = Exclude<ComponentType, "Form">;

interface PreviewPaneProps {
  spec: JsonRenderSpec | null;
  selectedElementId?: string | null;
  onFieldClick: (elementId: string) => void;
  onAddField: (type: EditableComponentType) => void;
  onReorderFields: (newOrder: string[]) => void;
  /** Action buttons rendered in the bottom-right toolbar of the pane (e.g. Save). */
  actions?: React.ReactNode;
}

const wrapperStyle: React.CSSProperties = {
  height: "100%",
  display: "flex",
  flexDirection: "column",
  minHeight: 0,
};

const toolbarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
  gap: 8,
  padding: "8px 16px",
  background: "#f5f5f5",
  borderTop: "1px solid var(--fidesui-color-border)",
  flexShrink: 0,
  minHeight: 48,
};

const canvasStyle: React.CSSProperties = {
  background: "#f5f5f5",
  width: "100%",
  flex: 1,
  minHeight: 0,
  padding: 32,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  overflowY: "auto",
};

const formCardStyle: React.CSSProperties = {
  background: "white",
  width: "100%",
  maxWidth: 360,
  padding: 32,
  borderRadius: 4,
  boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
};

const FIELD_TYPE_LABELS: Record<EditableComponentType, string> = {
  Text: "Text input",
  Select: "Single-select dropdown",
  MultiSelect: "Multi-select dropdown",
  Location: "Location picker",
};

const fieldTypeMenuItems = (
  Object.keys(catalog.components).filter(
    (k) => k !== "Form",
  ) as EditableComponentType[]
).map((type) => ({
  key: type,
  label: FIELD_TYPE_LABELS[type],
}));

const AddFieldButton = ({
  onAddField,
}: {
  onAddField: (type: EditableComponentType) => void;
}) => (
  <Dropdown
    menu={{
      items: fieldTypeMenuItems,
      onClick: ({ key }) => onAddField(key as EditableComponentType),
    }}
  >
    <Button data-testid="add-field-button" type="dashed" block>
      + Add field
    </Button>
  </Dropdown>
);

// Build a single-element spec for one field so the Renderer can render
// it in isolation. visible/watch are stripped because the admin preview
// always shows fields unconditionally — the Save modal warns about
// dropped conditional features.
const singleFieldSpec = (
  spec: JsonRenderSpec,
  elementId: string,
): JsonRenderSpec | null => {
  const element = spec.elements[elementId];
  if (!element) {
    return null;
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { visible, watch, ...rest } =
    element as JsonRenderSpec["elements"][string] & {
      visible?: unknown;
      watch?: unknown;
    };
  return {
    root: elementId,
    elements: { [elementId]: rest },
  };
};

export const PreviewPane = ({
  spec,
  selectedElementId,
  onFieldClick,
  onAddField,
  onReorderFields,
  actions,
}: PreviewPaneProps) => {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const childIds = spec?.elements[spec.root]?.children ?? [];
  const hasFields = childIds.length > 0;

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) {
      return;
    }
    const oldIndex = childIds.indexOf(active.id as string);
    const newIndex = childIds.indexOf(over.id as string);
    if (oldIndex < 0 || newIndex < 0) {
      return;
    }
    onReorderFields(arrayMove(childIds, oldIndex, newIndex));
  };

  return (
    <div style={wrapperStyle}>
      <div style={canvasStyle}>
        <div style={formCardStyle}>
          {hasFields && spec ? (
            <Form layout="vertical" style={{ marginBottom: 16 }}>
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={childIds}
                  strategy={verticalListSortingStrategy}
                >
                  {childIds.map((childId) => {
                    const subSpec = singleFieldSpec(spec, childId);
                    if (!subSpec) {
                      return null;
                    }
                    return (
                      <SortableFieldItem
                        key={childId}
                        id={childId}
                        selected={childId === selectedElementId}
                        onSelect={onFieldClick}
                      >
                        <JSONUIProvider registry={registry}>
                          <Renderer spec={subSpec as any} registry={registry} />
                        </JSONUIProvider>
                      </SortableFieldItem>
                    );
                  })}
                </SortableContext>
              </DndContext>
            </Form>
          ) : (
            <Empty
              description="No fields yet. Add one below or chat with the builder."
              style={{ marginBottom: 16 }}
            />
          )}
          <AddFieldButton onAddField={onAddField} />
        </div>
      </div>
      <div style={toolbarStyle} data-testid="preview-toolbar">
        {actions}
      </div>
    </div>
  );
};
