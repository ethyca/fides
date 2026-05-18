import { Button, Flex, Form, Input, Select, useMessage } from "fidesui";
import { useEffect, useState } from "react";

import DataUseSelect from "~/features/common/dropdown/DataUseSelect";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import {
  useAddSystemAssetMutation,
  useUpdateSystemAssetsMutation,
} from "~/features/system/system-assets.slice";
import { Asset } from "~/types/api";

interface AddEditAssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  systemKey: string;
  asset?: Asset;
}

const FORM_COPY = `Create and configure assets (e.g. cookies, pixels, tags) for this system to ensure proper consent enforcement. Adding assets manually allows you to define key attributes, assign categories, and align them with compliance requirements.`;

export enum AssetType {
  COOKIE = "Cookie",
  BROWSER_REQUEST = "Browser Request",
  I_FRAME = "iFrame",
  JAVASCRIPT_TAG = "Javascript tag",
  IMAGE = "Image",
}

const DEFAULT_VALUES: Asset = {
  name: "",
  description: "",
  duration: "",
  data_uses: [] as string[],
  domain: "",
  asset_type: "",
  id: "",
  system_id: "",
};

const AddEditAssetModal = ({
  isOpen,
  onClose,
  systemKey,
  asset,
}: AddEditAssetModalProps) => {
  const isCreate = !asset;
  const [form] = Form.useForm<Asset>();
  const watchedValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, watchedValues]);

  const [addSystemAsset, { isLoading: addIsLoading }] =
    useAddSystemAssetMutation();
  const [updateSystemAsset, { isLoading: updateIsLoading }] =
    useUpdateSystemAssetsMutation();
  const message = useMessage();

  const initialValues = asset ?? DEFAULT_VALUES;

  const handleFinish = async (values: Asset) => {
    const payload = asset ? { ...asset, ...values } : values;
    const result = isCreate
      ? await addSystemAsset({ systemKey, asset: payload })
      : await updateSystemAsset({ systemKey, assets: [payload] });

    if (isErrorResult(result)) {
      message.error(
        getErrorMessage(
          result.error,
          "An unexpected error occurred while saving this asset. Please try again.",
        ),
      );
      return;
    }
    message.success(
      isCreate ? "Asset added successfully" : "Asset updated successfully",
    );
    onClose();
  };

  return (
    <ConfirmCloseModal
      title={isCreate ? "Add asset" : "Edit asset"}
      onClose={onClose}
      getIsDirty={() => form.isFieldsTouched()}
      open={isOpen}
      centered
      destroyOnHidden
      footer={null}
      data-testid="add-modal-content"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleFinish}
        key={asset?.id ?? "create"}
        requiredMark
      >
        <Flex vertical className="pb-6 pt-4">
          <FormInfoBox>{FORM_COPY}</FormInfoBox>
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Enter a name for this asset" }]}
          >
            <Input disabled={!isCreate} data-testid="input-name" />
          </Form.Item>
          <Form.Item
            name="asset_type"
            label="Asset type"
            rules={[{ required: true, message: "Select an asset type" }]}
          >
            <Select
              aria-label="Asset type"
              options={enumToOptions(AssetType)}
              disabled={!isCreate}
              data-testid="controlled-select-asset_type"
            />
          </Form.Item>
          <Form.Item
            name="data_uses"
            label="Data uses"
            required
            rules={[
              {
                validator: (_, value) =>
                  value && value.length > 0
                    ? Promise.resolve()
                    : Promise.reject(new Error("Select at least one data use")),
              },
            ]}
          >
            <DataUseSelect
              aria-label="Data uses"
              mode="multiple"
              selectedTaxonomies={[]}
              variant="outlined"
              autoFocus={false}
              data-testid="controlled-select-data_uses"
            />
          </Form.Item>
          <Form.Item
            name="domain"
            label="Domain"
            rules={[
              {
                required: true,
                message: "Enter a valid domain for this asset",
              },
            ]}
          >
            <Input disabled={!isCreate} data-testid="input-domain" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea data-testid="input-description" />
          </Form.Item>
          <Form.Item
            shouldUpdate={(prev, next) => prev.asset_type !== next.asset_type}
            noStyle
          >
            {({ getFieldValue }) => {
              const assetType = getFieldValue("asset_type");
              if (!assetType) {
                return null;
              }
              if (assetType === AssetType.COOKIE) {
                return (
                  <Form.Item
                    name="duration"
                    label="Duration"
                    tooltip="Cookie duration is how long a cookie stays stored in the user's browser before automatically expiring and being deleted."
                  >
                    <Input
                      placeholder="e.g. '1 day', '30 minutes', '1 year'"
                      data-testid="input-duration"
                    />
                  </Form.Item>
                );
              }
              return (
                <Form.Item
                  name="base_url"
                  label="Base URL"
                  rules={[{ required: true, message: "Base URL is required" }]}
                  validateTrigger={["onChange", "onBlur"]}
                >
                  <Input data-testid="input-base_url" />
                </Form.Item>
              );
            }}
          </Form.Item>
        </Flex>
        <Flex justify="space-between">
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={addIsLoading || updateIsLoading}
            disabled={!submittable || (isCreate && !form.isFieldsTouched())}
            data-testid="save-btn"
          >
            Save
          </Button>
        </Flex>
      </Form>
    </ConfirmCloseModal>
  );
};

export default AddEditAssetModal;
