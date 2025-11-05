import {
  AntButton as Button,
  AntFlex as Flex,
  AntMessageInstance as MessageInstance,
  AntModal as Modal,
  AntTypography as Typography,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { DetailsDrawer } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer";
import { DetailsDrawerProps } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer/types";
import CustomTaxonomyDetails from "~/features/taxonomy/components/CustomTaxonomyDetails";
import {
  useDeleteCustomTaxonomyMutation,
  useUpdateCustomTaxonomyMutation,
} from "~/features/taxonomy/taxonomy.slice";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

interface CustomTaxonomyEditDrawerProps
  extends Omit<DetailsDrawerProps, "itemKey"> {
  taxonomy?: TaxonomyResponse | null;
  onDelete: () => void;
  messageApi: MessageInstance;
}

const FORM_ID = "custom-taxonomy-form";

const CustomTaxonomyEditDrawer = ({
  taxonomy,
  onClose,
  onDelete,
  messageApi,
  ...props
}: CustomTaxonomyEditDrawerProps) => {
  const [updateCustomTaxonomy, { isLoading: isUpdating }] =
    useUpdateCustomTaxonomyMutation();
  const [deleteCustomTaxonomy, { isLoading: isDeleting }] =
    useDeleteCustomTaxonomyMutation();

  const [modal, modalContext] = Modal.useModal();

  const handleUpdate = async (values: TaxonomyUpdate) => {
    if (!taxonomy?.fides_key) {
      messageApi.error("Taxonomy not found");
      return;
    }
    const result = await updateCustomTaxonomy({
      fides_key: taxonomy.fides_key,
      ...values,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy updated successfully");
  };

  const handleDelete = async () => {
    if (!taxonomy?.fides_key) {
      messageApi.error("Taxonomy not found");
      return;
    }
    const result = await deleteCustomTaxonomy(taxonomy.fides_key);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy deleted successfully");
    onDelete();
  };

  const confirmDelete = () => {
    modal.confirm({
      title: `Delete ${taxonomy?.name}?`,
      icon: null,
      content: (
        <Typography.Paragraph>
          Are you sure you want to delete this taxonomy? This action cannot be
          undone.
        </Typography.Paragraph>
      ),
      okText: "Delete",
      okType: "primary",
      onOk: handleDelete,
      centered: true,
    });
  };

  return (
    <>
      {modalContext}
      <DetailsDrawer
        title={`Edit ${taxonomy?.name}`}
        {...props}
        itemKey=""
        open={!!taxonomy}
        onClose={onClose}
        destroyOnHidden
        footer={
          <Flex justify="space-between" className="w-full">
            <Button loading={isDeleting} onClick={confirmDelete}>
              Delete
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              form={FORM_ID}
              loading={isUpdating}
            >
              Save
            </Button>
          </Flex>
        }
      >
        <CustomTaxonomyDetails
          taxonomy={taxonomy}
          onSubmit={handleUpdate}
          formId={FORM_ID}
        />
      </DetailsDrawer>
    </>
  );
};

export default CustomTaxonomyEditDrawer;
