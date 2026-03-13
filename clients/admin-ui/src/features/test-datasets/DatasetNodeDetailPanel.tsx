import { Drawer, Form, Input, Select, Tag, Typography } from "fidesui";
import { useEffect } from "react";

import { DatasetCollection, DatasetField } from "~/types/api";

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

const DatasetNodeDetailPanel = ({
  open,
  onClose,
  nodeData,
  onUpdateCollection,
  onUpdateField,
}: DatasetNodeDetailPanelProps) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (!nodeData || !open) {
      return;
    }

    if (nodeData.nodeType === "collection") {
      form.setFieldsValue({
        name: nodeData.collection.name,
        description: nodeData.collection.description ?? "",
        data_categories: nodeData.collection.data_categories ?? [],
      });
    } else {
      form.setFieldsValue({
        name: nodeData.field.name,
        description: nodeData.field.description ?? "",
        data_categories: nodeData.field.data_categories ?? [],
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

    const updates = {
      description: (allValues.description as string) || null,
      data_categories:
        (allValues.data_categories as string[])?.length > 0
          ? (allValues.data_categories as string[])
          : null,
    };

    if (nodeData.nodeType === "collection") {
      onUpdateCollection(nodeData.collection.name, updates);
    } else {
      onUpdateField(nodeData.collectionName, nodeData.fieldPath, updates);
    }
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

          {isProtected && (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              This field is protected and cannot be deleted, but you can edit
              its metadata.
            </Typography.Text>
          )}
        </Form>
      )}
    </Drawer>
  );
};

export default DatasetNodeDetailPanel;
