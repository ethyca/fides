import { Box, EditIcon, IconButton } from "@fidesui/react";
import { GearLightIcon } from "common/Icon";
import React from "react";

import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";

const PropertyActions = ({ id }) => (
    <Box py={2}>
      <IconButton
        aria-label="Install property"
        variant="outline"
        size="xs"
        marginRight="10px"
        icon={<GearLightIcon />}
      />
      <IconButton
        aria-label="Edit property"
        variant="outline"
        size="xs"
        marginRight="10px"
        icon={<EditIcon />}
      />
      <IconButton
        aria-label="Delete property"
        variant="outline"
        size="xs"
        marginRight="10px"
        icon={<TrashCanOutlineIcon />}
      />
    </Box>
  );

export default PropertyActions;
