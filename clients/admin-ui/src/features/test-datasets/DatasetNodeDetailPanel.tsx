import {
  Button,
  Collapse,
  Drawer,
  Flex,
  Form,
  Icons,
  Input,
  Select,
  Switch,
  Tag,
  Typography,
  useModal,
} from "fidesui";
import {
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

import { DatasetCollection, DatasetField } from "~/types/api";

import DatasetEditorActionsContext from "./context/DatasetEditorActionsContext";
import FieldMetadataFormItems, {
  buildFieldMeta,
  DataCategoryTagSelect,
} from "./FieldMetadataFormItems";
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
  allowNameEditing?: boolean;
}

export interface DatasetNodeDetailPanelHandle {
  flush: () => void;
}

const DatasetNodeDetailPanel = forwardRef<
  DatasetNodeDetailPanelHandle,
  DatasetNodeDetailPanelProps
>(
  (
    {
      open,
      onClose,
      nodeData,
      onUpdateCollection,
      onUpdateField,
      allowNameEditing = false,
    },
    ref,
  ) => {
    const [form] = Form.useForm();
    const modal = useModal();
    const actions = useContext(DatasetEditorActionsContext);

    // Snapshot of form values when the panel opens, used to skip
    // no-op updates on close.
    const initialValuesRef = useRef<string>("");

    // Initialize form values when a node is selected
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
          data_type: field.fides_meta?.data_type ?? undefined,
          identity: field.fides_meta?.identity ?? "",
          primary_key: field.fides_meta?.primary_key ?? false,
          read_only: field.fides_meta?.read_only ?? false,
          redact: field.fides_meta?.redact ?? "",
        });
      }
      initialValuesRef.current = JSON.stringify(form.getFieldsValue());
      // Only run when a different node is selected, not on every nodeData
      // reference change. nodeData identity changes on parent re-renders but
      // the logical node (identified by open + selectedNodeId) stays the same.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, form]);

    // Commit all form values to the dataset (skips if nothing changed)
    const flush = useCallback(() => {
      if (!nodeData) {
        return;
      }

      const allValues = form.getFieldsValue();
      if (JSON.stringify(allValues) === initialValuesRef.current) {
        return;
      }
      const categories = allValues.data_categories as string[] | undefined;
      const newName = allValues.name as string | undefined;
      const baseUpdates = {
        ...(newName ? { name: newName } : {}),
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
        onUpdateField(nodeData.collectionName, nodeData.fieldPath, {
          ...baseUpdates,
          fides_meta: buildFieldMeta(allValues),
        } as Partial<DatasetField>);
      }
    }, [nodeData, onUpdateCollection, onUpdateField, form]);

    // Expose flush() so the parent can call it before clearing selection
    useImperativeHandle(ref, () => ({ flush }), [flush]);

    // Flush and close — called from the Drawer's onClose and Done button
    const handleClose = useCallback(() => {
      flush();
      onClose();
    }, [flush, onClose]);

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
          <Flex align="center" gap={8}>
            {nodeData?.nodeType === "collection" ? (
              <Icons.Table size={16} />
            ) : (
              <Icons.Column size={16} />
            )}
            <Typography.Text strong>{nodeData?.label}</Typography.Text>
            <Tag
              color={nodeData?.nodeType === "collection" ? "minos" : "default"}
            >
              {nodeData?.nodeType}
            </Tag>
            {isProtected && <Tag color="warning">protected</Tag>}
          </Flex>
        }
        placement="right"
        width={400}
        open={open}
        onClose={handleClose}
        mask={false}
      >
        {nodeData && (
          <Form form={form} layout="vertical" size="small">
            <Form.Item label="Name" name="name">
              <Input disabled={!allowNameEditing} aria-label="Name" />
            </Form.Item>

            <Form.Item label="Description" name="description">
              <Input.TextArea rows={3} placeholder="Add a description..." />
            </Form.Item>

            <Form.Item label="Data Categories" name="data_categories">
              <DataCategoryTagSelect />
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
                    children: <FieldMetadataFormItems />,
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

            <Flex
              gap={8}
              style={{ marginTop: 24 }}
              justify={isProtected ? "end" : "space-between"}
            >
              {!isProtected && (
                <Button danger size="small" onClick={handleDelete}>
                  Delete {nodeData.nodeType}
                </Button>
              )}
              <Button type="primary" size="small" onClick={handleClose}>
                Done
              </Button>
            </Flex>
          </Form>
        )}
      </Drawer>
    );
  },
);

DatasetNodeDetailPanel.displayName = "DatasetNodeDetailPanel";

export default DatasetNodeDetailPanel;
