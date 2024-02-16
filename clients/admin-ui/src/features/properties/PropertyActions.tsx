import { Box, EditIcon, IconButton } from "@fidesui/react";
import React from "react";
import { useRouter } from "next/router";
import NewJavaScriptTag from "../privacy-experience/NewJavaScriptTag";
import { Property } from "~/pages/consent/properties/types";
import { PROPERTIES_ROUTE } from "../common/nav/v2/routes";

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
