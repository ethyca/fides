import { Text, Tooltip, useDisclosure, useToast, WarningIcon } from "fidesui";
import router from "next/router";
import React from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useDeletePropertyMutation } from "~/features/properties/property.slice";
import { Property, ScopeRegistryEnum } from "~/types/api";

interface Props {
  property: Property;
  triggerComponent: React.ReactElement & { isDisabled?: boolean };
}

/**
 * A component that encapsulates the logic to display the "delete property" modal.
 * It accepts a triggerComponent prop that will be used as the button to trigger the modal.
 * The triggerComponent should implement the isDisabled prop to indicate if it should be disabled.
 *
 * @param property The property associated with the modal.
 * @param triggerComponent The React component to be rendered as the trigger for the modals.
 *
 * @example
 * <DeletePropertyModal
 *   property={selectedProperty}
 *   triggerComponent={<Button>Delete Property</Button>}
 * />
 */
const DeletePropertyModal = ({ property, triggerComponent }: Props) => {
  const toast = useToast();
  const confirmationModal = useDisclosure();
  const [deletePropertyMutationTrigger] = useDeletePropertyMutation();

  const disabled = property.experiences.length > 0;

  const handleModalOpen = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.stopPropagation();
    if (!disabled) {
      confirmationModal.onOpen();
    }
  };

  const handleConfirm = async () => {
    confirmationModal.onClose();
    const result = await deletePropertyMutationTrigger(property.id!);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    router.push(`${PROPERTIES_ROUTE}`);
    toast(successToastParams(`Property ${property.name} deleted successfully`));
  };

  return (
    <Restrict scopes={[ScopeRegistryEnum.PROPERTY_DELETE]}>
      <Tooltip
        label="All of the experiences on this property must be unlinked before the property can be deleted."
        placement="right"
        isDisabled={!disabled}
      >
        <span>
          {React.cloneElement(triggerComponent, {
            onClick: handleModalOpen,
            disabled,
          })}
        </span>
      </Tooltip>
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        onClose={confirmationModal.onClose}
        onConfirm={handleConfirm}
        title={`Delete ${property.name}`}
        message={
          <Text color="gray.500">
            You are about to delete property {property.name}. This action is not
            reversible and will result in {property.name} no longer being
            available for your data governance. Are you sure you want to
            proceed?
          </Text>
        }
        continueButtonText="Ok"
        isCentered
        icon={<WarningIcon />}
      />
    </Restrict>
  );
};

export default DeletePropertyModal;
