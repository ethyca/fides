import {
  Text,
  Tooltip,
  useDisclosure,
  useToast,
  WarningIcon,
} from "@fidesui/react";
import router from "next/router";
import React from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { Property, ScopeRegistryEnum } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { PROPERTIES_ROUTE } from "../common/nav/v2/routes";
import Restrict from "../common/Restrict";
import { errorToastParams, successToastParams } from "../common/toast";
import { useDeletePropertyMutation } from "./property.slice";

interface Props {
  property: Property;
  displayComponent: React.ReactElement & { isDisabled?: boolean };
}

/**
 * A component that encapsulates the logic to display the "delete property" modal.
 * It accepts a displayComponent prop that will be used as the button to trigger the modal.
 * The displayComponent should implement the isDisabled prop to indicate if it should be disabled.
 *
 * @param property The property associated with the modal.
 * @param displayComponent The React component to be rendered as the trigger for the modals.
 *
 * @example
 * <DeletePropertyModalTrigger
 *   property={selectedProperty}
 *   displayComponent={<Button>Delete Property</Button>}
 * />
 */
const DeletePropertyModalTrigger: React.FC<Props> = ({
  property,
  displayComponent,
}) => {
  const toast = useToast();
  const confirmationModal = useDisclosure();
  const [deletePropertyMutationTrigger] = useDeletePropertyMutation();

  const isDisabled = property.experiences.length > 0;

  const handleModalOpen = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.stopPropagation();
    if (!isDisabled) {
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
        isDisabled={!isDisabled}
      >
        <span>
          {React.cloneElement(displayComponent, {
            onClick: handleModalOpen,
            isDisabled,
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

export default DeletePropertyModalTrigger;
