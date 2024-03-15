import { Box, EditIcon, IconButton } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import Restrict from "~/features/common/Restrict";
import NewJavaScriptTag from "~/features/privacy-experience/NewJavaScriptTag";
import { Property, ScopeRegistryEnum } from "~/types/api";

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
        <IconButton
          aria-label="Edit property"
          variant="outline"
          size="xs"
          marginRight="10px"
          icon={<EditIcon />}
          onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
            e.stopPropagation();
            handleEdit();
          }}
        />
      </Restrict>
    </Box>
  );
};

export default PropertyActions;
