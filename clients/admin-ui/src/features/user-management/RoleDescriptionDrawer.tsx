import { Box, VStack } from "fidesui";

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
          padding={4}
          borderRadius="md"
          backgroundColor="gray.75"
          fontSize="14px"
        >
          <Box fontWeight="semibold">{role.label}</Box>
          <Box color="gray.700">{role.description}</Box>
        </Box>
      ))}
    </VStack>
  </Box>
);

export default RoleDescriptionDrawer;
