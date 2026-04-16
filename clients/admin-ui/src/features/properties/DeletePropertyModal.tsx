import { ChakraText as Text, Tooltip, useMessage, useModal } from "fidesui";
import router from "next/router";
import React from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { useDeletePropertyMutation } from "~/features/properties/property.slice";
import { Property, ScopeRegistryEnum } from "~/types/api";

interface Props {
  property: Property;
  triggerComponent: React.ReactElement<{
    onClick?: (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
    disabled?: boolean;
  }>;
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
  const message = useMessage();
  const modal = useModal();
  const [deletePropertyMutationTrigger] = useDeletePropertyMutation();

  const disabled = property.experiences.length > 0;

  const handleModalOpen = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.stopPropagation();
    if (!disabled) {
      modal.confirm({
        title: `Delete ${property.name}`,
        content: (
          <Text color="gray.500">
            You are about to delete property {property.name}. This action is not
            reversible and will result in {property.name} no longer being
            available for your data governance. Are you sure you want to
            proceed?
          </Text>
        ),
        okText: "Ok",
        centered: true,
        onOk: async () => {
          const result = await deletePropertyMutationTrigger(property.id!);
          if (isErrorResult(result)) {
            message.error(getErrorMessage(result.error));
            return;
          }
          router.push(`${PROPERTIES_ROUTE}`);
          message.success(`Property ${property.name} deleted successfully`);
        },
      });
    }
  };

  return (
    <Restrict scopes={[ScopeRegistryEnum.PROPERTY_DELETE]}>
      <Tooltip
        title={
          !disabled
            ? undefined
            : "All of the experiences on this property must be unlinked before the property can be deleted."
        }
        placement="right"
      >
        <span>
          {React.cloneElement(triggerComponent, {
            onClick: handleModalOpen,
            disabled,
          })}
        </span>
      </Tooltip>
    </Restrict>
  );
};

export default DeletePropertyModal;
