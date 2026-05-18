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
import { Button, Dropdown, Empty, Form, Switch, Typography } from "fidesui";
import React from "react";

import type { ComponentType } from "./catalog";
import { catalog } from "./catalog";
import type { JsonRenderSpec } from "./types";
import { registry } from "./registry";
import { SortableFieldItem } from "./SortableFieldItem";

type EditableComponentType = Exclude<ComponentType, "Form">;

export type PreviewMode = "edit" | "preview";

/**
 * Action-level copy that PC renders around the form: description above,
 * description_subtext paragraphs, and the Cancel / Continue button labels.
 * Read-only in the builder — managed via the action edit modal — but shown
 * in Preview mode so authors see what end users actually see.
 */
export interface ActionCopy {
  description?: string | null;
  description_subtext?: string[] | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
}

interface PreviewPaneProps {
  spec: JsonRenderSpec | null;
  selectedElementId?: string | null;
  /**
   * Action-level copy (description, subtext, button labels). Rendered in
   * Preview mode only, around the custom fields, mirroring PC.
   */
  actionCopy?: ActionCopy | null;
  onFieldClick: (elementId: string) => void;
  onAddField: (type: EditableComponentType) => void;
  onReorderFields: (newOrder: string[]) => void;
  /** Action buttons rendered in the bottom-right toolbar of the pane (e.g. Save). */
  actions?: React.ReactNode;
  /**
   * "edit" (default) renders fields one-at-a-time wrapped in SortableFieldItem
   * with all visibility conditions stripped, so authors can edit any field.
   * "preview" renders the spec straight through, honoring `visible` so the
   * builder shows what an end user would see.
   */
  previewMode?: PreviewMode;
  onPreviewModeChange?: (next: PreviewMode) => void;
}

const wrapperStyle: React.CSSProperties = {
  height: "100%",
  display: "flex",
  flexDirection: "column",
  minHeight: 0,
};

const toolbarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  padding: "8px 16px",
  background: "#f5f5f5",
  borderTop: "1px solid var(--fidesui-color-border)",
  flexShrink: 0,
  minHeight: 48,
};

const toolbarSideStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
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
  Radio: "Radio group",
  Location: "Location picker",
  Email: "Email",
  Name: "Name",
  Phone: "Phone",
};

// Fixed element IDs for identity types — used to detect duplicates in the spec.
const IDENTITY_ELEMENT_IDS: Partial<Record<EditableComponentType, string>> = {
  Email: "f_email",
  Name: "f_name",
  Phone: "f_phone",
};

// Identity types in the canonical PC render order (Name → Email → Phone).
const IDENTITY_TYPES_ORDERED: EditableComponentType[] = [
  "Name",
  "Email",
  "Phone",
];
const IDENTITY_TYPE_SET = new Set<string>(IDENTITY_TYPES_ORDERED);

// Custom (non-identity) types in alphabetical order.
const CUSTOM_TYPES_ORDERED: EditableComponentType[] = (
  Object.keys(catalog.components).filter(
    (k) => k !== "Form" && !IDENTITY_TYPE_SET.has(k),
  ) as EditableComponentType[]
).sort();

const AddFieldButton = ({
  onAddField,
  spec,
}: {
  onAddField: (type: EditableComponentType) => void;
  spec: JsonRenderSpec | null;
}) => {
  const availableIdentity = IDENTITY_TYPES_ORDERED.filter((type) => {
    const fixedId = IDENTITY_ELEMENT_IDS[type];
    return !fixedId || !spec?.elements[fixedId];
  });

  const identityItems = availableIdentity.map((type) => ({
    key: type,
    label: <strong>{FIELD_TYPE_LABELS[type]}</strong>,
  }));

  const customItems = CUSTOM_TYPES_ORDERED.map((type) => ({
    key: type,
    label: FIELD_TYPE_LABELS[type],
  }));

  const items = [
    ...identityItems,
    ...(identityItems.length > 0 && customItems.length > 0
      ? [{ type: "divider" as const }]
      : []),
    ...customItems,
  ];

  return (
    <Dropdown
      menu={{
        items,
        onClick: ({ key }) => onAddField(key as EditableComponentType),
      }}
    >
      <Button data-testid="add-field-button" type="dashed" block>
        + Add field
      </Button>
    </Dropdown>
  );
};

// Build a single-element spec for one field so the Renderer can render
// it in isolation. visible/watch are stripped because Edit mode shows
// fields unconditionally — the Save modal warns about dropped conditional
// features. Preview mode uses the full spec (see renderPreview below).
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
  previewMode = "edit",
  onPreviewModeChange,
  actionCopy,
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

  const renderEditCanvas = () => (
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
      <AddFieldButton onAddField={onAddField} spec={spec} />
    </div>
  );

  // Preview mode: render the entire spec through one JSONUIProvider so the
  // shared state model can resolve cross-field $state references (e.g.
  // "show this field when /form/country eq 'US'"). Drop any field marked
  // `hidden` from the rendered tree — hidden fields are query-param-driven
  // and never visible to end users, so they shouldn't show in Preview either.
  const previewSpec = React.useMemo(() => {
    if (!spec) {
      return null;
    }
    const rootChildren = spec.elements[spec.root]?.children ?? [];
    const visibleChildIds = rootChildren.filter((id) => {
      const el = spec.elements[id];
      return !(el && (el.props as { hidden?: boolean }).hidden === true);
    });
    if (visibleChildIds.length === rootChildren.length) {
      return spec;
    }
    return {
      ...spec,
      elements: {
        ...spec.elements,
        [spec.root]: {
          ...spec.elements[spec.root],
          children: visibleChildIds,
        },
      },
    };
  }, [spec]);

  const description = actionCopy?.description?.trim();
  const subtext = (actionCopy?.description_subtext ?? []).filter(
    (line): line is string => typeof line === "string" && line.length > 0,
  );
  const confirmLabel = actionCopy?.confirmButtonText || "Continue";
  const cancelLabel = actionCopy?.cancelButtonText || "Cancel";

  const renderPreviewCanvas = () => (
    <div style={formCardStyle}>
      {(description || subtext.length > 0) && (
        <div style={{ marginBottom: 16 }}>
          {description && (
            <Typography.Paragraph
              style={{ marginBottom: subtext.length ? 8 : 0 }}
            >
              {description}
            </Typography.Paragraph>
          )}
          {subtext.map((line, i) => (
            <Typography.Paragraph
              // eslint-disable-next-line react/no-array-index-key
              key={i}
              type="secondary"
              style={{ marginBottom: i === subtext.length - 1 ? 0 : 8 }}
            >
              {line}
            </Typography.Paragraph>
          ))}
        </div>
      )}
      {hasFields && previewSpec ? (
        <JSONUIProvider registry={registry}>
          <Renderer spec={previewSpec as any} registry={registry} />
        </JSONUIProvider>
      ) : (
        <Empty description="No fields yet. Switch to Edit to add one." />
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <Button block disabled>
          {cancelLabel}
        </Button>
        <Button type="primary" block disabled>
          {confirmLabel}
        </Button>
      </div>
    </div>
  );

  return (
    <div style={wrapperStyle}>
      <div style={canvasStyle}>
        {previewMode === "edit" ? renderEditCanvas() : renderPreviewCanvas()}
      </div>
      <div style={toolbarStyle} data-testid="preview-toolbar">
        <div style={toolbarSideStyle}>
          <Typography.Text>Preview mode</Typography.Text>
          <Switch
            checked={previewMode === "preview"}
            onChange={(checked) =>
              onPreviewModeChange?.(checked ? "preview" : "edit")
            }
            data-testid="preview-mode-toggle"
            aria-label="Toggle preview mode"
          />
        </div>
        <div style={toolbarSideStyle}>{actions}</div>
      </div>
    </div>
  );
};
