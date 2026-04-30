import {
  Alert,
  Button,
  Flex,
  Modal,
  Space,
  Splitter,
  useMessage,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

import type { ComponentType } from "./catalog";
import { ChatPane } from "./ChatPane";
import { detectDrift } from "./drift";
import { FieldPropertiesPanel } from "./FieldPropertiesPanel";
import type { DroppedFeature, JsonRenderSpec, PcCustomFields } from "./mapper";
import { mapSpecToPcShape } from "./mapper";
import { PreviewPane } from "./PreviewPane";
import {
  addField as addFieldMutation,
  removeField as removeFieldMutation,
  reorderFields as reorderFieldsMutation,
  updateField as updateFieldMutation,
} from "./specMutations";
import { synthesizeSpecFromPcShape } from "./synthesize";
import { useFormBuilder } from "./useFormBuilder";

type EditableComponentType = Exclude<ComponentType, "Form">;

interface ActionShape {
  policy_key?: string;
  custom_privacy_request_fields?: PcCustomFields;
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
    richSpec: JsonRenderSpec;
  }) => Promise<void>;
}

const describeDropped = (d: DroppedFeature): string => {
  switch (d.kind) {
    case "visible":
      return `visible expression on ${d.elementId}`;
    case "watch":
      return `watch expression on ${d.elementId}`;
    case "expression":
      return `expression in props.${d.path} on ${d.elementId}`;
    case "unknown_component":
      return `unknown component ${d.type} on ${d.elementId}`;
    default:
      return JSON.stringify(d);
  }
};

const splitterStyle: React.CSSProperties = {
  height: "calc(100vh - 240px)",
  minHeight: 480,
};

const stickyFooterStyle: React.CSSProperties = {
  borderTop: "1px solid var(--fidesui-color-border)",
  backgroundColor: "var(--fidesui-color-bg-container)",
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
    if (action?.custom_privacy_request_fields) {
      return synthesizeSpecFromPcShape(action.custom_privacy_request_fields);
    }
    return null;
  }, [action]);

  const driftDetected = useMemo(() => {
    /* eslint-disable no-underscore-dangle */
    if (!action?._form_builder_spec?.spec) {
      return false;
    }
    return detectDrift(
      action._form_builder_spec.spec,
      action.custom_privacy_request_fields ?? {},
    );
    /* eslint-enable no-underscore-dangle */
  }, [action]);

  const builder = useFormBuilder({
    propertyId,
    actionPolicyKey,
    initialSpec,
  });

  const [confirmingDropped, setConfirmingDropped] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(
    null,
  );

  const handleAddField = useCallback(
    (type: EditableComponentType) => {
      const { spec: nextSpec, elementId } = addFieldMutation(
        builder.spec,
        type,
      );
      builder.setSpec(nextSpec);
      setSelectedElementId(elementId);
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

  if (!action) {
    return <Alert type="error" message="Action not found on property." />;
  }

  const persist = async () => {
    if (!builder.spec) {
      return;
    }
    const result = mapSpecToPcShape(builder.spec);
    if (result.errors.length > 0) {
      message.error("Form has validation errors — fix before saving.");
      return;
    }
    setSaving(true);
    try {
      await onSave({
        actionPolicyKey,
        pcShape: result.pcShape,
        richSpec: builder.spec,
      });
      message.success("Saved");
    } finally {
      setSaving(false);
      setConfirmingDropped(false);
    }
  };

  const handleSave = () => {
    if (!builder.spec) {
      return;
    }
    const result = mapSpecToPcShape(builder.spec);
    if (result.droppedFeatures.length > 0) {
      setConfirmingDropped(true);
      return;
    }
    persist();
  };

  const droppedSummary: DroppedFeature[] = builder.spec
    ? mapSpecToPcShape(builder.spec).droppedFeatures
    : [];

  const handleRebuild = () => {
    if (action.custom_privacy_request_fields) {
      builder.setSpec(
        synthesizeSpecFromPcShape(action.custom_privacy_request_fields),
      );
      setSelectedElementId(null);
    }
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      {driftDetected && (
        <Alert
          type="warning"
          message="Saved builder state differs from saved fields. The builder is showing the rich saved state."
          action={
            <Button size="small" onClick={handleRebuild}>
              Rebuild from saved fields
            </Button>
          }
        />
      )}
      <Splitter style={splitterStyle}>
        <Splitter.Panel
          defaultSize="25%"
          min={0}
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
        <Splitter.Panel min={240} data-testid="preview-panel">
          <PreviewPane
            spec={builder.spec}
            selectedElementId={selectedElementId}
            onFieldClick={handleSelectField}
            onAddField={handleAddField}
            onReorderFields={handleReorderFields}
          />
        </Splitter.Panel>
        <Splitter.Panel
          defaultSize="30%"
          min={0}
          collapsible
          data-testid="properties-panel"
        >
          <FieldPropertiesPanel
            spec={builder.spec}
            selectedElementId={selectedElementId}
            onUpdateField={handleUpdateField}
            onRemoveField={handleRemoveField}
          />
        </Splitter.Panel>
      </Splitter>
      <Flex
        justify="flex-end"
        gap="small"
        className="sticky bottom-0 z-10 px-4 py-2"
        style={stickyFooterStyle}
      >
        <Button
          type="primary"
          onClick={handleSave}
          loading={saving}
          data-testid="save-button"
        >
          Save
        </Button>
      </Flex>
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
            <li key={idx}>{describeDropped(d)}</li>
          ))}
        </ul>
      </Modal>
    </Space>
  );
};
