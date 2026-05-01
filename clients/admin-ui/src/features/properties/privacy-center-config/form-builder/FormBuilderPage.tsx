import { Alert, Button, Col, Modal, Row, Space, useMessage } from "fidesui";
import { useMemo, useState } from "react";

import { ChatPane } from "./ChatPane";
import { detectDrift } from "./drift";
import type { DroppedFeature, JsonRenderSpec, PcCustomFields } from "./mapper";
import { mapSpecToPcShape } from "./mapper";
import { PreviewPane } from "./PreviewPane";
import { synthesizeSpecFromPcShape } from "./synthesize";
import { useFormBuilder } from "./useFormBuilder";

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

export const FormBuilderPage: React.FC<FormBuilderPageProps> = ({
  propertyId,
  property,
  actionPolicyKey,
  onSave,
}) => {
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

  const handleClickField = (elementId: string) => {
    const element = builder.spec?.elements?.[elementId];
    if (!element) {
      return;
    }
    const name = (element.props as Record<string, unknown> | undefined)
      ?.name as string | undefined;
    if (!name) {
      return;
    }
    builder.sendMessage(`Edit the field "${name}". Tell me what changed.`);
  };

  const droppedSummary: DroppedFeature[] = builder.spec
    ? mapSpecToPcShape(builder.spec).droppedFeatures
    : [];

  const handleRebuild = () => {
    if (action.custom_privacy_request_fields) {
      builder.setSpec(
        synthesizeSpecFromPcShape(action.custom_privacy_request_fields),
      );
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
      <Row gutter={16} style={{ height: "calc(100vh - 200px)" }}>
        <Col span={10} style={{ display: "flex", flexDirection: "column" }}>
          <ChatPane
            messages={builder.messages}
            status={builder.status}
            error={builder.error}
            onSend={builder.sendMessage}
            onAbort={builder.abort}
          />
        </Col>
        <Col span={14} style={{ display: "flex", flexDirection: "column" }}>
          <PreviewPane spec={builder.spec} onFieldClick={handleClickField} />
        </Col>
      </Row>
      <Button type="primary" onClick={handleSave} loading={saving}>
        Save
      </Button>
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
