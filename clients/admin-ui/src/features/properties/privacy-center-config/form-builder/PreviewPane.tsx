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
import { Button, Empty, Flex, Form, Switch, Typography } from "fidesui";
import React from "react";

import { AddFieldButton } from "./AddFieldButton";
import type { ComponentType } from "./catalog";
import styles from "./PreviewPane.module.scss";
import { registry } from "./registry";
import { SortableFieldItem } from "./SortableFieldItem";
import type { JsonRenderSpec } from "./types";

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
    <div className={styles.formCard}>
      {hasFields && spec ? (
        <Form layout="vertical" className="mb-4">
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
          className="mb-4"
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
    <div className={styles.formCard}>
      {(description || subtext.length > 0) && (
        <Flex vertical className="mb-4">
          {description && (
            <Typography.Paragraph className={subtext.length ? "mb-2" : "m-0"}>
              {description}
            </Typography.Paragraph>
          )}
          {subtext.map((line, i) => (
            <Typography.Paragraph
              // eslint-disable-next-line react/no-array-index-key
              key={i}
              type="secondary"
              className={i === subtext.length - 1 ? "m-0" : "mb-2"}
            >
              {line}
            </Typography.Paragraph>
          ))}
        </Flex>
      )}
      {hasFields && previewSpec ? (
        <JSONUIProvider registry={registry}>
          <Renderer spec={previewSpec as any} registry={registry} />
        </JSONUIProvider>
      ) : (
        <Empty description="No fields yet. Switch to Edit to add one." />
      )}
      <Flex gap="small" className="mt-4">
        <Button block disabled>
          {cancelLabel}
        </Button>
        <Button type="primary" block disabled>
          {confirmLabel}
        </Button>
      </Flex>
    </div>
  );

  return (
    <Flex vertical className="h-full min-h-0">
      <div className={styles.canvas}>
        {previewMode === "edit" ? renderEditCanvas() : renderPreviewCanvas()}
      </div>
      <div className={styles.toolbar} data-testid="preview-toolbar">
        <Flex align="center" gap="small">
          <Typography.Text>Preview mode</Typography.Text>
          <Switch
            checked={previewMode === "preview"}
            onChange={(checked) =>
              onPreviewModeChange?.(checked ? "preview" : "edit")
            }
            data-testid="preview-mode-toggle"
            aria-label="Toggle preview mode"
          />
        </Flex>
        <Flex align="center" gap="small">
          {actions}
        </Flex>
      </div>
    </Flex>
  );
};
