import {
  AntButton,
  AntFlex,
  Collapse,
  ModalProps,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import FormModal from "~/features/common/modals/FormModal";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useAddSystemAssetMutation,
  useUpdateSystemAssetsMutation,
} from "~/features/system/system-assets.slice";
import WrappedConsentCategorySelect from "~/features/system/tabs/system-assets/WrappedConsentCategorySelect";
import { Asset } from "~/types/api";

interface AddEditAssetModalProps extends Omit<ModalProps, "children"> {
  systemKey: string;
  asset?: Asset;
}

const FORM_COPY = `Create and configure assets (e.g. cookies, pixels, tags) for this system to ensure proper consent enforcement. Adding assets manually allows you to define key attributes, assign categories, and align them with compliance requirements.`;

enum AssetType {
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
  data_uses: Yup.array().min(1, "Select at least one category of consent"),
  base_url: Yup.string().when("asset_type", {
    is: (asset_type: string) => asset_type !== AssetType.COOKIE,
    then: (schema) => schema.required("Base URL is required"),
    otherwise: (schema) => schema.notRequired(),
  }),
});

const DEFAULT_VALUES: Asset = {
  name: "",
  description: "",
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
  ...props
}: AddEditAssetModalProps) => {
  const isCreate = !asset;

  const [addSystemAsset, { isLoading: addIsLoading }] =
    useAddSystemAssetMutation();
  const [updateSystemAsset, { isLoading: updateIsLoading }] =
    useUpdateSystemAssetsMutation();
  const toast = useToast();

  const handleCreateNew = async (values: Asset) => {
    const result = await addSystemAsset({ systemKey, asset: values });
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(
        result.error,
        "An unexpected error occurred while saving this asset. Please try again.",
      );
      toast(errorToastParams(errorMsg));
    } else {
      toast(successToastParams("Asset added successfully"));
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
      toast(errorToastParams(errorMsg));
    } else {
      toast(successToastParams("Asset updated successfully"));
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

  const initialValues: Asset = asset ?? DEFAULT_VALUES;

  return (
    <FormModal
      title={isCreate ? "Add asset" : "Edit asset"}
      onClose={onClose}
      isOpen={isOpen}
      {...props}
    >
      <Formik
        initialValues={initialValues}
        onSubmit={handleSaveClicked}
        validationSchema={validationSchema}
      >
        {({ values, isValid, dirty }) => {
          return (
            <Form>
              <AntFlex vertical className="pb-6 pt-4">
                <FormInfoBox>
                  <Text fontSize="sm">{FORM_COPY}</Text>
                </FormInfoBox>
                <AntFlex vertical gap={20}>
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
                  <WrappedConsentCategorySelect
                    name="data_uses"
                    label="Categories of consent"
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
                  <Collapse
                    in={
                      !!values.asset_type &&
                      values.asset_type !== AssetType.COOKIE
                    }
                  >
                    <CustomTextInput
                      id="base_url"
                      name="base_url"
                      label="Base URL"
                      variant="stacked"
                      isRequired={
                        !!values.asset_type &&
                        values.asset_type !== AssetType.COOKIE
                      }
                    />
                  </Collapse>
                </AntFlex>
              </AntFlex>
              <AntFlex justify="space-between">
                <AntButton onClick={onClose}>Cancel</AntButton>
                <AntButton
                  type="primary"
                  htmlType="submit"
                  loading={addIsLoading || updateIsLoading}
                  disabled={!isValid || !dirty}
                  data-testid="save-btn"
                >
                  Save
                </AntButton>
              </AntFlex>
            </Form>
          );
        }}
      </Formik>
    </FormModal>
  );
};

export default AddEditAssetModal;
