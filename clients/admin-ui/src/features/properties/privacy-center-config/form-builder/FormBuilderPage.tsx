import { Alert, Button, Modal, Splitter, useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  FormGuard,
  useIsAnyFormDirty,
} from "~/features/common/hooks/useIsAnyFormDirty";

import type { ComponentType } from "./catalog";
import { ChatPane } from "./ChatPane";
import { detectSpecPcShapeDrift, stableJson } from "./drift";
import { FieldPropertiesPanel } from "./FieldPropertiesPanel";
import { jsonSpecToPcShape } from "./jsonSpecToPcShape";
import { pcShapeToJsonSpec } from "./pcShapeToJsonSpec";
import { type PreviewMode, PreviewPane } from "./PreviewPane";
import {
  addField as addFieldMutation,
  defaultSpec,
  removeField as removeFieldMutation,
  reorderFields as reorderFieldsMutation,
  setFieldVisibility as setFieldVisibilityMutation,
  updateField as updateFieldMutation,
} from "./specMutations";
import type { DroppedFeature, JsonRenderSpec, PcCustomFields } from "./types";
import { useFormBuilder } from "./useFormBuilder";

type EditableComponentType = Exclude<ComponentType, "Form">;

interface ActionShape {
  policy_key?: string;
  description?: string | null;
  description_subtext?: string[] | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
  custom_privacy_request_fields?: PcCustomFields;
  identity_inputs?: Record<string, "required" | "optional"> | null;
  field_order?: string[] | null;
  // eslint-disable-next-line no-underscore-dangle
  _form_builder_spec?: { spec: JsonRenderSpec; version: number };
}

interface FormBuilderPageProperty {
  id: string;
  name: string;
  privacy_center_config: {
    actions?: ActionShape[];
  } | null;
}

interface FormBuilderPageProps {
  propertyId: string;
  property: FormBuilderPageProperty;
  actionPolicyKey: string;
  onSave: (next: {
    actionPolicyKey: string;
    pcShape: PcCustomFields;
    identityInputs: Record<string, "required" | "optional">;
    fieldOrder: string[];
    richSpec: JsonRenderSpec;
  }) => Promise<void>;
}

const fieldLabel = (spec: JsonRenderSpec | null, elementId: string): string => {
  const props = (spec?.elements?.[elementId]?.props ?? {}) as {
    name?: string;
    label?: string;
  };
  return props.label ?? props.name ?? elementId;
};

const describeDropped = (
  d: DroppedFeature,
  spec: JsonRenderSpec | null,
): string => {
  switch (d.kind) {
    case "visible":
      return `Conditional visibility on "${fieldLabel(spec, d.elementId)}" couldn't be translated to the privacy center schema — the field will render unconditionally for end users.`;
    case "watch":
      return `Watch expression on "${fieldLabel(spec, d.elementId)}" — preserved in the builder only.`;
    case "expression":
      return `Dynamic expression in props.${d.path} on "${fieldLabel(spec, d.elementId)}" — preserved in the builder only.`;
    case "unknown_component":
      return `Unknown component ${d.type} on "${fieldLabel(spec, d.elementId)}" — won't render outside the builder.`;
    default:
      return JSON.stringify(d);
  }
};

const rootStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  flex: 1,
  minHeight: 0,
  width: "100%",
};

const splitterStyle: React.CSSProperties = {
  flex: 1,
  minHeight: 0,
  border: "1px solid var(--fidesui-color-border)",
  borderRadius: 4,
  overflow: "hidden",
};

export const FormBuilderPage = ({
  propertyId,
  property,
  actionPolicyKey,
  onSave,
}: FormBuilderPageProps) => {
  const message = useMessage();

  const action = useMemo(
    () =>
      (property.privacy_center_config?.actions ?? []).find(
        (a) => a.policy_key === actionPolicyKey,
      ),
    [property, actionPolicyKey],
  );

  const initialSpec = useMemo<JsonRenderSpec | null>(() => {
    /* eslint-disable no-underscore-dangle */
    if (action?._form_builder_spec?.spec) {
      return action._form_builder_spec.spec;
    }
    /* eslint-enable no-underscore-dangle */
    if (action?.custom_privacy_request_fields || action?.identity_inputs) {
      return pcShapeToJsonSpec(
        action.custom_privacy_request_fields ?? {},
        action.identity_inputs,
        action.field_order,
      );
    }
    // No saved fields yet — seed with the standard DSR defaults so the
    // builder isn't empty on first load.
    return defaultSpec();
  }, [action]);

  const builder = useFormBuilder({
    propertyId,
    actionPolicyKey,
    initialSpec,
  });

  // Drift = the saved rich spec doesn't round-trip cleanly to the saved
  // legacy `custom_privacy_request_fields`. Comparing live `builder.spec`
  // would flag every unsaved edit, so we compare the persisted pair only.
  const savedDrift = useMemo(() => {
    /* eslint-disable no-underscore-dangle */
    if (!action?._form_builder_spec?.spec) {
      return false;
    }
    return detectSpecPcShapeDrift(
      action._form_builder_spec.spec,
      action.custom_privacy_request_fields ?? {},
    );
    /* eslint-enable no-underscore-dangle */
  }, [action]);

  // Rebuild swaps the in-memory spec; the persisted state is unchanged
  // until Save. Suppress the alert in the meantime so the user isn't
  // told their reconciled state still drifts.
  const [driftAcknowledged, setDriftAcknowledged] = useState(false);
  const driftDetected = savedDrift && !driftAcknowledged;

  const [confirmingDropped, setConfirmingDropped] = useState(false);
  const [saving, setSaving] = useState(false);
  // Pre-select the first field on initial load so the properties panel
  // isn't empty. Subsequent changes (add/remove/select) are user-driven.
  const [selectedElementId, setSelectedElementId] = useState<string | null>(
    () => initialSpec?.elements[initialSpec.root]?.children[0] ?? null,
  );
  const [previewMode, setPreviewMode] = useState<PreviewMode>("edit");

  const handleAddField = useCallback(
    (type: EditableComponentType) => {
      const { spec: nextSpec, elementId } = addFieldMutation(
        builder.spec,
        type,
      );
      builder.setSpec(nextSpec);
      setSelectedElementId(elementId);
      // Move focus to the newly added field card after React mounts it,
      // so keyboard users land on the new field (and onFocus auto-selects).
      requestAnimationFrame(() => {
        const node = document.querySelector<HTMLElement>(
          `[data-testid="sortable-field-${elementId}"]`,
        );
        node?.focus();
      });
    },
    [builder],
  );

  const handleSelectField = useCallback((elementId: string) => {
    setSelectedElementId(elementId);
  }, []);

  const handleUpdateField = useCallback(
    (elementId: string, props: Record<string, unknown>) => {
      if (!builder.spec) {
        return;
      }
      builder.setSpec(updateFieldMutation(builder.spec, elementId, props));
    },
    [builder],
  );

  const handleRemoveField = useCallback(
    (elementId: string) => {
      if (!builder.spec) {
        return;
      }
      builder.setSpec(removeFieldMutation(builder.spec, elementId));
      setSelectedElementId((current) =>
        current === elementId ? null : current,
      );
    },
    [builder],
  );

  const handleReorderFields = useCallback(
    (newOrder: string[]) => {
      if (!builder.spec) {
        return;
      }
      builder.setSpec(reorderFieldsMutation(builder.spec, newOrder));
    },
    [builder],
  );

  const handleUpdateVisibility = useCallback(
    (elementId: string, visible: unknown | undefined) => {
      if (!builder.spec) {
        return;
      }
      builder.setSpec(
        setFieldVisibilityMutation(builder.spec, elementId, visible),
      );
    },
    [builder],
  );

  // Dirty = current spec differs from the spec the page loaded with.
  // Compare via stable JSON so reordered keys don't flag false-positives.
  const isDirty = useMemo(
    () => stableJson(builder.spec) !== stableJson(initialSpec),
    [builder.spec, initialSpec],
  );

  // Block Next.js navigation away when the form is dirty.
  // Pattern: synchronously abort the routeChangeStart, show the existing
  // Unsaved Changes modal via attemptAction, then re-push to the intended
  // path if the user confirms. The bypassNavigationRef keeps the second
  // push from re-triggering the guard.
  const router = useRouter();
  const { attemptAction } = useIsAnyFormDirty();
  const bypassNavigationRef = useRef(false);
  useEffect(() => {
    const handleRouteChange = (nextPath: string) => {
      if (bypassNavigationRef.current) {
        bypassNavigationRef.current = false;
        return;
      }
      if (!isDirty || nextPath === router.asPath) {
        return;
      }
      // Show the modal and re-attempt navigation if confirmed.
      attemptAction().then((confirmed) => {
        if (confirmed) {
          bypassNavigationRef.current = true;
          router.push(nextPath);
        }
      });
      router.events.emit("routeChangeError");
      // eslint-disable-next-line @typescript-eslint/no-throw-literal
      throw "Route change aborted by FormGuard (safe to ignore).";
    };
    router.events.on("routeChangeStart", handleRouteChange);
    return () => {
      router.events.off("routeChangeStart", handleRouteChange);
    };
  }, [router, attemptAction, isDirty]);

  // Browser refresh / tab close.
  useEffect(() => {
    if (!isDirty) {
      return undefined;
    }
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers ignore the return value but require preventDefault();
      // older Chromium needs returnValue to be a non-empty string.
      // eslint-disable-next-line no-param-reassign
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  if (!action) {
    return <Alert type="error" title="Action not found on property." />;
  }

  const persist = async () => {
    if (!builder.spec) {
      return;
    }
    const result = jsonSpecToPcShape(builder.spec);
    if (result.errors.length > 0) {
      message.error("Form has validation errors — fix before saving.");
      return;
    }
    const identityValues = Object.values(result.identityInputs);
    if (identityValues.length === 0) {
      message.error(
        "Add at least one identity field (Email, Name, or Phone) before saving.",
      );
      return;
    }
    if (!identityValues.some((v) => v === "required")) {
      message.error(
        "At least one identity field must be set to required before saving.",
      );
      return;
    }
    setSaving(true);
    try {
      await onSave({
        actionPolicyKey,
        pcShape: result.pcShape,
        identityInputs: result.identityInputs,
        fieldOrder: result.fieldOrder,
        richSpec: builder.spec,
      });
      // Save just wrote rich + legacy in lockstep, so any prior drift is
      // resolved. Acknowledge it now so the warning hides immediately,
      // even if the property refetch hasn't returned yet.
      setDriftAcknowledged(true);
      message.success("Saved");
    } catch (err: unknown) {
      const detail =
        typeof err === "string"
          ? err
          : err instanceof Error
            ? err.message
            : undefined;
      message.error(detail ? `Failed to save: ${detail}` : "Failed to save");
    } finally {
      setSaving(false);
      setConfirmingDropped(false);
    }
  };

  const handleSave = () => {
    if (!builder.spec) {
      return;
    }
    const result = jsonSpecToPcShape(builder.spec);
    if (result.droppedFeatures.length > 0) {
      setConfirmingDropped(true);
      return;
    }
    persist();
  };

  const droppedSummary: DroppedFeature[] = builder.spec
    ? jsonSpecToPcShape(builder.spec).droppedFeatures
    : [];

  const handleRebuild = () => {
    if (action.custom_privacy_request_fields || action.identity_inputs) {
      builder.setSpec(
        pcShapeToJsonSpec(
          action.custom_privacy_request_fields ?? {},
          action.identity_inputs,
        ),
      );
      setSelectedElementId(null);
      setDriftAcknowledged(true);
    }
  };

  return (
    <div style={rootStyle}>
      <FormGuard
        id={`form-builder-${propertyId}-${actionPolicyKey}`}
        name={`Form editor (${actionPolicyKey})`}
        isDirty={isDirty}
      />
      {driftDetected && (
        <Alert
          type="warning"
          showIcon
          title="This form was edited outside this editor"
          description="The editor is showing the configuration from your last edit here. Newer changes were saved elsewhere. Reset to load those instead."
          action={
            <Button size="small" onClick={handleRebuild}>
              Reset to latest saved fields
            </Button>
          }
        />
      )}
      <Splitter style={splitterStyle}>
        <Splitter.Panel
          defaultSize="25%"
          min={240}
          collapsible
          data-testid="chat-panel"
        >
          <ChatPane
            messages={builder.messages}
            status={builder.status}
            error={builder.error}
            onSend={builder.sendMessage}
            onAbort={builder.abort}
          />
        </Splitter.Panel>
        <Splitter.Panel min={400} data-testid="preview-panel">
          <PreviewPane
            spec={builder.spec}
            selectedElementId={selectedElementId}
            actionCopy={
              action
                ? {
                    description: action.description,
                    description_subtext: action.description_subtext,
                    confirmButtonText: action.confirmButtonText,
                    cancelButtonText: action.cancelButtonText,
                  }
                : null
            }
            onFieldClick={handleSelectField}
            onAddField={handleAddField}
            onReorderFields={handleReorderFields}
            previewMode={previewMode}
            onPreviewModeChange={setPreviewMode}
            actions={
              <>
                <Button
                  onClick={() => router.push(`/properties/${propertyId}`)}
                  data-testid="cancel-button"
                >
                  Cancel
                </Button>
                <Button
                  type="primary"
                  onClick={handleSave}
                  loading={saving}
                  data-testid="save-button"
                >
                  Save
                </Button>
              </>
            }
          />
        </Splitter.Panel>
        <Splitter.Panel
          defaultSize="25%"
          min={240}
          collapsible
          data-testid="properties-panel"
        >
          <FieldPropertiesPanel
            spec={builder.spec}
            selectedElementId={selectedElementId}
            onUpdateField={handleUpdateField}
            onRemoveField={handleRemoveField}
            onUpdateVisibility={handleUpdateVisibility}
          />
        </Splitter.Panel>
      </Splitter>
      <Modal
        open={confirmingDropped}
        title="Some features won't be saved"
        onOk={persist}
        confirmLoading={saving}
        onCancel={() => setConfirmingDropped(false)}
        okText="Save anyway"
      >
        <p>
          The privacy center renderer doesn&apos;t support these features yet.
          They&apos;ll stay in the builder preview, but won&apos;t reach end
          users on save:
        </p>
        <ul>
          {droppedSummary.map((d, idx) => (
            // eslint-disable-next-line react/no-array-index-key
            <li key={idx}>{describeDropped(d, builder.spec)}</li>
          ))}
        </ul>
      </Modal>
    </div>
  );
};
