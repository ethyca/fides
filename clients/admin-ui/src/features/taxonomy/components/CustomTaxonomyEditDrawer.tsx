import {
  AntButton as Button,
  AntFlex as Flex,
  AntMessage as message,
  AntModal as Modal,
} from "fidesui";
import { useState } from "react";

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
  taxonomy?: TaxonomyResponse;
  onDelete: () => void;
}

const FORM_ID = "custom-taxonomy-form";

const CustomTaxonomyEditDrawer = ({
  taxonomy,
  onClose,
  onDelete,
  ...props
}: CustomTaxonomyEditDrawerProps) => {
  const [messageApi, messageContext] = message.useMessage();

  const [updateCustomTaxonomy, { isLoading: isUpdating }] =
    useUpdateCustomTaxonomyMutation();
  const [deleteCustomTaxonomy, { isLoading: isDeleting }] =
    useDeleteCustomTaxonomyMutation();

  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const handleUpdate = async (values: TaxonomyUpdate) => {
    const result = await updateCustomTaxonomy({
      fides_key: taxonomy?.fides_key as string,
      ...values,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy updated successfully");
  };

  const handleDelete = async () => {
    const result = await deleteCustomTaxonomy(taxonomy?.fides_key as string);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy deleted successfully");
    setDeleteModalIsOpen(false);
    onDelete();
  };

  return (
    <>
      {messageContext}
      <DetailsDrawer
        title={`Edit ${taxonomy?.name}`}
        {...props}
        itemKey=""
        open={!!taxonomy}
        destroyOnHidden
        footer={
          <Flex justify="space-between" className="w-full">
            <Button
              loading={isDeleting}
              onClick={() => setDeleteModalIsOpen(true)}
            >
              Delete
            </Button>
            <Modal
              title={`Delete ${taxonomy?.name}?`}
              open={deleteModalIsOpen}
              onCancel={() => setDeleteModalIsOpen(false)}
              onOk={handleDelete}
              okText="Delete"
              cancelText="Cancel"
              loading={isDeleting}
              centered
            >
              Are you sure you want to delete this taxonomy? This action cannot
              be undone.
            </Modal>
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
