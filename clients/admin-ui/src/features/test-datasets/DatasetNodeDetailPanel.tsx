import {
  Button,
  Collapse,
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  Tag,
  Typography,
  useModal,
} from "fidesui";
import { useContext, useEffect } from "react";

import { DatasetCollection, DatasetField } from "~/types/api";

import DatasetEditorActionsContext from "./context/DatasetEditorActionsContext";
import { CollectionNodeData, FieldNodeData } from "./useDatasetGraph";

interface DatasetNodeDetailPanelProps {
  open: boolean;
  onClose: () => void;
  nodeData: CollectionNodeData | FieldNodeData | null;
  onUpdateCollection: (
    collectionName: string,
    updates: Partial<DatasetCollection>,
  ) => void;
  onUpdateField: (
    collectionName: string,
    fieldPath: string,
    updates: Partial<DatasetField>,
  ) => void;
}

const DATA_TYPE_OPTIONS = [
  "string",
  "integer",
  "float",
  "boolean",
  "object_id",
  "object",
].map((v) => ({ label: v, value: v }));

const REDACT_OPTIONS = [
  { label: "None", value: "" },
  { label: "name", value: "name" },
];

const DatasetNodeDetailPanel = ({
  open,
  onClose,
  nodeData,
  onUpdateCollection,
  onUpdateField,
}: DatasetNodeDetailPanelProps) => {
  const [form] = Form.useForm();
  const modal = useModal();
  const actions = useContext(DatasetEditorActionsContext);

  useEffect(() => {
    if (!nodeData || !open) {
      return;
    }

    if (nodeData.nodeType === "collection") {
      const { collection } = nodeData;
      form.setFieldsValue({
        name: collection.name,
        description: collection.description ?? "",
        data_categories: collection.data_categories ?? [],
        // CollectionMeta fields
        after: collection.fides_meta?.after ?? [],
        erase_after: collection.fides_meta?.erase_after ?? [],
        skip_processing: collection.fides_meta?.skip_processing ?? false,
      });
    } else {
      const { field } = nodeData;
      form.setFieldsValue({
        name: field.name,
        description: field.description ?? "",
        data_categories: field.data_categories ?? [],
        // FidesMeta fields
        data_type: field.fides_meta?.data_type ?? undefined,
        identity: field.fides_meta?.identity ?? "",
        primary_key: field.fides_meta?.primary_key ?? false,
        read_only: field.fides_meta?.read_only ?? false,
        return_all_elements: field.fides_meta?.return_all_elements ?? false,
        length: field.fides_meta?.length ?? undefined,
        custom_request_field: field.fides_meta?.custom_request_field ?? "",
        redact: field.fides_meta?.redact ?? "",
      });
    }
  }, [nodeData, open, form]);

  const handleValuesChange = (
    _: Record<string, unknown>,
    allValues: Record<string, unknown>,
  ) => {
    if (!nodeData) {
      return;
    }

    const categories = allValues.data_categories as string[] | undefined;
    const baseUpdates = {
      description: (allValues.description as string) || undefined,
      data_categories:
        categories && categories.length > 0 ? categories : undefined,
    };

    if (nodeData.nodeType === "collection") {
      const after = allValues.after as string[] | undefined;
      const eraseAfter = allValues.erase_after as string[] | undefined;
      const skipProcessing = allValues.skip_processing as boolean;
      const collectionMeta = {
        after: after && after.length > 0 ? after : undefined,
        erase_after:
          eraseAfter && eraseAfter.length > 0 ? eraseAfter : undefined,
        skip_processing: skipProcessing || undefined,
      };
      const hasAnyMeta = Object.values(collectionMeta).some(
        (v) => v !== undefined,
      );

      onUpdateCollection(nodeData.collection.name, {
        ...baseUpdates,
        fides_meta: hasAnyMeta ? collectionMeta : undefined,
      } as Partial<DatasetCollection>);
    } else {
      const redactVal = allValues.redact as string;
      const fieldMeta = {
        data_type: (allValues.data_type as string) || undefined,
        identity: (allValues.identity as string) || undefined,
        primary_key: (allValues.primary_key as boolean) || undefined,
        read_only: (allValues.read_only as boolean) || undefined,
        return_all_elements:
          (allValues.return_all_elements as boolean) || undefined,
        length:
          allValues.length !== null &&
          allValues.length !== undefined &&
          allValues.length !== ""
            ? (allValues.length as number)
            : undefined,
        custom_request_field:
          (allValues.custom_request_field as string) || undefined,
        redact: redactVal === "name" ? ("name" as const) : undefined,
      };
      const hasAnyMeta = Object.values(fieldMeta).some((v) => v !== undefined);

      onUpdateField(nodeData.collectionName, nodeData.fieldPath, {
        ...baseUpdates,
        fides_meta: hasAnyMeta ? fieldMeta : undefined,
      } as Partial<DatasetField>);
    }
  };

  const handleDelete = () => {
    if (!nodeData) {
      return;
    }
    modal.confirm({
      title: `Delete this ${nodeData.nodeType}?`,
      content:
        nodeData.nodeType === "collection"
          ? "This will remove the collection and all its fields."
          : "This will remove the field.",
      okText: "Delete",
      okButtonProps: { danger: true },
      onOk: () => {
        if (nodeData.nodeType === "collection") {
          actions.deleteCollection(nodeData.collection.name);
        } else {
          actions.deleteField(nodeData.collectionName, nodeData.fieldPath);
        }
        onClose();
      },
    });
  };

  const isProtected = nodeData?.nodeType === "field" && nodeData.isProtected;

  return (
    <Drawer
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Typography.Text strong>{nodeData?.label}</Typography.Text>
          <Tag
            color={nodeData?.nodeType === "collection" ? "minos" : "default"}
          >
            {nodeData?.nodeType}
          </Tag>
          {isProtected && <Tag color="warning">protected</Tag>}
        </div>
      }
      placement="right"
      width={400}
      open={open}
      onClose={onClose}
      mask={false}
    >
      {nodeData && (
        <Form
          form={form}
          layout="vertical"
          onValuesChange={handleValuesChange}
          size="small"
        >
          <Form.Item label="Name" name="name">
            <Input disabled aria-label="Name" />
          </Form.Item>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} placeholder="Add a description..." />
          </Form.Item>

          <Form.Item label="Data Categories" name="data_categories">
            <Select
              mode="tags"
              placeholder="Add data categories..."
              aria-label="Data Categories"
              style={{ width: "100%" }}
            />
          </Form.Item>

          {nodeData.nodeType === "collection" && (
            <Collapse
              size="small"
              items={[
                {
                  key: "collection-meta",
                  label: "Collection Metadata (fides_meta)",
                  children: (
                    <>
                      <Form.Item label="After" name="after">
                        <Select
                          mode="tags"
                          placeholder="Collections to run after..."
                          aria-label="After"
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                      <Form.Item label="Erase After" name="erase_after">
                        <Select
                          mode="tags"
                          placeholder="Collections to erase after..."
                          aria-label="Erase After"
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                      <Form.Item
                        label="Skip Processing"
                        name="skip_processing"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Skip Processing" />
                      </Form.Item>
                    </>
                  ),
                },
              ]}
            />
          )}

          {nodeData.nodeType === "field" && (
            <Collapse
              size="small"
              items={[
                {
                  key: "field-meta",
                  label: "Field Metadata (fides_meta)",
                  children: (
                    <>
                      <Form.Item label="Data Type" name="data_type">
                        <Select
                          allowClear
                          placeholder="Select data type..."
                          aria-label="Data Type"
                          options={DATA_TYPE_OPTIONS}
                        />
                      </Form.Item>
                      <Form.Item label="Identity" name="identity">
                        <Input placeholder="e.g. email, phone_number" />
                      </Form.Item>
                      <Form.Item
                        label="Primary Key"
                        name="primary_key"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Primary Key" />
                      </Form.Item>
                      <Form.Item
                        label="Read Only"
                        name="read_only"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Read Only" />
                      </Form.Item>
                      <Form.Item
                        label="Return All Elements"
                        name="return_all_elements"
                        valuePropName="checked"
                      >
                        <Switch aria-label="Return All Elements" />
                      </Form.Item>
                      <Form.Item label="Length" name="length">
                        <InputNumber
                          min={0}
                          placeholder="Max length"
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                      <Form.Item
                        label="Custom Request Field"
                        name="custom_request_field"
                      >
                        <Input placeholder="Custom field name" />
                      </Form.Item>
                      <Form.Item label="Redact" name="redact">
                        <Select aria-label="Redact" options={REDACT_OPTIONS} />
                      </Form.Item>
                    </>
                  ),
                },
              ]}
            />
          )}

          {isProtected && (
            <Typography.Text
              type="secondary"
              style={{ fontSize: 12, display: "block", marginTop: 16 }}
            >
              This field is protected and cannot be deleted, but you can edit
              its metadata.
            </Typography.Text>
          )}

          {!isProtected && (
            <div style={{ marginTop: 24 }}>
              <Button danger size="small" block onClick={handleDelete}>
                Delete {nodeData.nodeType}
              </Button>
            </div>
          )}
        </Form>
      )}
    </Drawer>
  );
};

export default DatasetNodeDetailPanel;
