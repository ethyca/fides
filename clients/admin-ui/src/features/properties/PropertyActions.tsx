import { AntButton as Button, Box, EditIcon } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
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
    <Box py={2}>
      <NewJavaScriptTag property={property} />
      <Restrict scopes={[ScopeRegistryEnum.PROPERTY_UPDATE]}>
        <Button
          aria-label="Edit property"
          data-testid="edit-property-button"
          size="small"
          className="mr-[10px]"
          icon={<EditIcon />}
          onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
            e.stopPropagation();
            handleEdit();
          }}
        />
      </Restrict>
      <DeletePropertyModal
        property={property}
        triggerComponent={
          <Button
            aria-label="Delete property"
            data-testid="delete-property-button"
            size="small"
            className="mr-[10px]"
            icon={<TrashCanOutlineIcon />}
          />
        }
      />
    </Box>
  );
};

export default PropertyActions;
