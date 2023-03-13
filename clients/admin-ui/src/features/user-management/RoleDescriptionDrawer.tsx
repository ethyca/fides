import { Box, VStack } from "@fidesui/react";

import { ROLES } from "~/types/api/models/RolesDataMapping";

const RoleDescriptionDrawer = () => (
  <Box>
    <Box pb={4} fontSize="18px" fontWeight="semibold">
      Role Description
    </Box>
    <VStack spacing={4}>
      {ROLES.map((role) => (
        <Box
          key={role.roleKey}
          padding="16px"
          backgroundColor="blue.50"
          fontSize="14px"
        >
          <Box fontWeight="semibold">{role.label}</Box>
          <Box color="gray.500">
            {role.description}
            Owners have view and edit access to the whole organization and can
            create new users
          </Box>
        </Box>
      ))}
    </VStack>
  </Box>
);

export default RoleDescriptionDrawer;
