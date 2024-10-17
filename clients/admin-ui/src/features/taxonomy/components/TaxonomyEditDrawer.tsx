import {
  ConfirmationModal,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "../../common/EditDrawer";
import useTaxonomySlices from "../hooks/useTaxonomySlices";
import { TaxonomyEntity } from "../types";
import { DefaultTaxonomyTypes } from "../types/DefaultTaxonomyTypes";
import TaxonomyEditForm from "./TaxonomyEditForm";

interface TaxonomyEditDrawerProps {
  taxonomyItem?: TaxonomyEntity | null;
  taxonomyType: DefaultTaxonomyTypes;
  onClose: () => void;
}

const TaxonomyEditDrawer = ({
  taxonomyItem,
  taxonomyType,
  onClose: closeDrawer,
}: TaxonomyEditDrawerProps) => {
  const FORM_ID = "edit-taxonomy-form";
  const isCustomTaxonomy = !taxonomyItem?.is_default;

  const toast = useToast();

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const { updateTrigger, deleteTrigger } = useTaxonomySlices({ taxonomyType });

  const handleEdit = async (updatedTaxonomy: TaxonomyEntity) => {
    const result = await updateTrigger(updatedTaxonomy);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    // TODO: Reimplement custom fields
    // if (customFields.isEnabled) {
    //   await customFields.upsertCustomFields(newValues);
    // }

    toast(successToastParams("Taxonomy successfully updated"));
    closeDrawer();
  };

  const handleDelete = async () => {
    await deleteTrigger(taxonomyItem!.fides_key);
    onDeleteClose();
    closeDrawer();
  };

  return (
    <>
      <EditDrawer
        isOpen={!!taxonomyItem}
        onClose={closeDrawer}
        header={<EditDrawerHeader title={taxonomyItem?.name || ""} />}
        footer={
          <EditDrawerFooter
            onClose={closeDrawer}
            onDelete={isCustomTaxonomy ? onDeleteOpen : undefined}
            formId={FORM_ID}
          />
        }
      >
        <div className="mb-4">
          <h3 className="mb-3 font-semibold text-gray-700">Details</h3>
          <div className="flex">
            <span className="w-1/3 text-sm text-gray-500">Fides key:</span>
            <span>{taxonomyItem?.fides_key}</span>
          </div>
          {/* <div className="flex">
            <span className=" w-1/3 text-sm text-gray-500">Qualifiers:</span>
            <span />
          </div> */}
        </div>
        <TaxonomyEditForm
          initialValues={taxonomyItem!}
          onSubmit={handleEdit}
          formId={FORM_ID}
          taxonomyType={taxonomyType}
        />
      </EditDrawer>

      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title={`Delete ${taxonomyType}`}
        message={
          <Stack>
            <Text>
              You are about to permanently delete the {taxonomyType}{" "}
              <Text color="complimentary.500" as="span" fontWeight="bold">
                {taxonomyItem?.name}
              </Text>{" "}
              from your taxonomy. Are you sure you would like to continue?
            </Text>
          </Stack>
        }
      />
    </>
  );
};
export default TaxonomyEditDrawer;
