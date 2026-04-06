import { Button, ChakraText as Text, Flex, useMessage } from "fidesui";
import { Form, FormikProvider, useFormik } from "formik";
import * as Yup from "yup";

import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import {
  useAddSystemAssetMutation,
  useUpdateSystemAssetsMutation,
} from "~/features/system/system-assets.slice";
import WrappedDataUseSelect from "~/features/system/tabs/system-assets/WrappedDataUseSelect";
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

const validationSchema = Yup.object().shape({
  name: Yup.string().required("Enter a name for this asset"),
  domain: Yup.string().required("Enter a valid domain for this asset"),
  asset_type: Yup.string().required("Select an asset type"),
  data_uses: Yup.array().min(1, "Select at least one data use"),
  base_url: Yup.string().when("asset_type", {
    is: (asset_type: string) => asset_type !== AssetType.COOKIE,
    then: (schema) => schema.required("Base URL is required"),
    otherwise: (schema) => schema.notRequired(),
  }),
});

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

  const [addSystemAsset, { isLoading: addIsLoading }] =
    useAddSystemAssetMutation();
  const [updateSystemAsset, { isLoading: updateIsLoading }] =
    useUpdateSystemAssetsMutation();
  const message = useMessage();

  const handleCreateNew = async (values: Asset) => {
    const result = await addSystemAsset({ systemKey, asset: values });
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        "An unexpected error occurred while saving this asset. Please try again.",
      );
      message.error(errorMsg);
    } else {
      message.success("Asset added successfully");
      onClose();
    }
  };

  const handleUpdate = async (values: Asset) => {
    const result = await updateSystemAsset({ systemKey, assets: [values] });
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        "An unexpected error occurred while saving this asset. Please try again.",
      );
      message.error(errorMsg);
    } else {
      message.success("Asset updated successfully");
      onClose();
    }
  };

  const handleSaveClicked = (values: Asset) => {
    if (isCreate) {
      handleCreateNew(values);
    } else {
      handleUpdate(values);
    }
  };

  const initialValues = asset ?? DEFAULT_VALUES;

  const formik = useFormik({
    initialValues,
    onSubmit: handleSaveClicked,
    validationSchema,
  });
  const { values, isValid, dirty } = formik;
  const isCookieAsset =
    !!values.asset_type && values.asset_type === AssetType.COOKIE;
  const isNotCookieAsset =
    !!values.asset_type && values.asset_type !== AssetType.COOKIE;

  return (
    <FormikProvider value={formik}>
      <ConfirmCloseModal
        title={isCreate ? "Add asset" : "Edit asset"}
        onClose={onClose}
        getIsDirty={() => formik.dirty}
        open={isOpen}
        centered
        destroyOnClose
        footer={null}
        data-testid="add-modal-content"
      >
        <Form>
              <Flex vertical className="pb-6 pt-4">
                <FormInfoBox>
                  <Text fontSize="sm">{FORM_COPY}</Text>
                </FormInfoBox>
                <Flex vertical gap={20}>
                  <CustomTextInput
                    id="name"
                    name="name"
                    label="Name"
                    variant="stacked"
                    isRequired
                    disabled={!isCreate}
                  />
                  <ControlledSelect
                    isRequired
                    id="asset_type"
                    name="asset_type"
                    label="Asset type"
                    options={enumToOptions(AssetType)}
                    layout="stacked"
                    disabled={!isCreate}
                  />
                  <WrappedDataUseSelect
                    name="data_uses"
                    label="Data uses"
                    layout="stacked"
                  />
                  <CustomTextInput
                    id="domain"
                    name="domain"
                    label="Domain"
                    variant="stacked"
                    isRequired
                    disabled={!isCreate}
                  />
                  <CustomTextArea
                    id="description"
                    name="description"
                    label="Description"
                    variant="stacked"
                  />
                  {isCookieAsset && (
                    <CustomTextInput
                      id="duration"
                      name="duration"
                      label="Duration"
                      variant="stacked"
                      placeholder="e.g. '1 day', '30 minutes', '1 year'"
                      tooltip="Cookie duration is how long a cookie stays stored in the user's browser before automatically expiring and being deleted."
                      isRequired={isCookieAsset}
                    />
                  )}
                  {isNotCookieAsset && (
                    <CustomTextInput
                      id="base_url"
                      name="base_url"
                      label="Base URL"
                      variant="stacked"
                      isRequired={isNotCookieAsset}
                    />
                  )}
                </Flex>
              </Flex>
              <Flex justify="space-between">
                <Button onClick={onClose}>Cancel</Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={addIsLoading || updateIsLoading}
                  disabled={!isValid || !dirty}
                  data-testid="save-btn"
                >
                  Save
                </Button>
              </Flex>
        </Form>
      </ConfirmCloseModal>
    </FormikProvider>
  );
};

export default AddEditAssetModal;
