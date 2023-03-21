import { Box, VStack } from "@fidesui/react";

import { ROLES } from "~/features/user-management/constants";

const RoleDescriptionDrawer = () => (
  <Box>
    <Box pb={4} fontSize="18px" fontWeight="semibold">
      Role Description
    </Box>
    <VStack spacing={4}>
      {ROLES.map((role) => (
        <Box
          width="100%"
          key={role.roleKey}
          padding="16px"
          backgroundColor="blue.50"
          fontSize="14px"
        >
          <Box fontWeight="semibold">{role.label}</Box>
          <Box color="gray.500">{role.description}</Box>
        </Box>
      ))}
    </VStack>
  </Box>
);

export default RoleDescriptionDrawer;
