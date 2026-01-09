import { Button, Flex, Icons } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import NewJavaScriptTag from "~/features/privacy-experience/NewJavaScriptTag";
import { Property, ScopeRegistryEnum } from "~/types/api";

import DeletePropertyModal from "./DeletePropertyModal";

interface Props {
  property: Property;
}

const PropertyActions = ({ property }: Props) => {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`${PROPERTIES_ROUTE}/${property.id}`);
  };

  return (
    <Flex gap="small">
      <NewJavaScriptTag property={property} />
      <Restrict scopes={[ScopeRegistryEnum.PROPERTY_UPDATE]}>
        <Button
          aria-label="Edit property"
          data-testid="edit-property-button"
          size="small"
          icon={<Icons.Edit />}
          onClick={handleEdit}
        />
      </Restrict>
      <DeletePropertyModal
        property={property}
        triggerComponent={
          <Button
            aria-label="Delete property"
            data-testid="delete-property-button"
            size="small"
            icon={<TrashCanOutlineIcon />}
          />
        }
      />
    </Flex>
  );
};

export default PropertyActions;
