import { Box, EditIcon, IconButton } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { Property } from "~/types/api";

import { PROPERTIES_ROUTE } from "../common/nav/v2/routes";
import NewJavaScriptTag from "../privacy-experience/NewJavaScriptTag";

interface Props {
  property: Property;
}

const PropertyActions = ({ property }: Props) => {
  const router = useRouter();

  const handleEdit = () => {
    router.push(`${PROPERTIES_ROUTE}/${property.key}`);
  };

  return (
    <Box py={2}>
      <NewJavaScriptTag property={property} />
      <IconButton
        aria-label="Edit property"
        variant="outline"
        size="xs"
        marginRight="10px"
        icon={<EditIcon />}
        onClick={handleEdit}
      />
    </Box>
  );
};

export default PropertyActions;
