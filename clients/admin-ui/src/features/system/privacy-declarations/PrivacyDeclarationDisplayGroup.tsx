import { PrivacyDeclarationResponse } from "~/types/api";
import { AddIcon, DeleteIcon } from "@chakra-ui/icons";
import {
  Text,
  Stack,
  Box,
  Heading,
  Button,
  IconButton,
  Divider,
  HStack,
  Spacer,
} from "@fidesui/react";

const PrivacyDeclarationRow = ({
  declaration,
  handleDelete,
}: {
  declaration: PrivacyDeclarationResponse;
  handleDelete: (dec: PrivacyDeclarationResponse) => void;
}) => {
  return (
    <>
      <Box px={6} py={4}>
        <HStack>
          <Text>{declaration.name}</Text>
          <Spacer />
          <IconButton
            aria-label="delete-declaration"
            variant="outline"
            size="sm"
            onClick={() => handleDelete(declaration)}
          >
            <DeleteIcon />
          </IconButton>
        </HStack>
      </Box>
      <Divider />
    </>
  );
};

const PrivacyDeclarationDisplayGroup = ({
  heading,
  declarations,
  handleAdd,
  handleDelete,
}: {
  heading: string;
  declarations: PrivacyDeclarationResponse[];
  handleAdd?: () => void;
  handleDelete: (dec: PrivacyDeclarationResponse) => void;
}) => (
  <Stack spacing={4}>
    <Box maxWidth="720px" border="1px" borderColor="gray.200" borderRadius={6}>
      <Box
        backgroundColor="gray.50"
        px={6}
        py={4}
        borderBottom="1px"
        borderColor="gray.200"
        borderTopRadius={6}
      >
        <Heading as="h3" size="xs">
          {heading}
        </Heading>
      </Box>

      <Stack spacing={0}>
        {declarations.map((pd) => (
          <PrivacyDeclarationRow declaration={pd} handleDelete={handleDelete} />
        ))}
      </Stack>
      <Box backgroundColor="gray.50" px={6} py={4} borderBottomRadius={6}>
        <Button
          onClick={handleAdd}
          size="xs"
          px={2}
          py={1}
          backgroundColor="primary.800"
          color="white"
          fontWeight="600"
        >
          <Text mr={2}>Add data use</Text>
          <AddIcon boxSize={3} color="white" />
        </Button>
      </Box>
    </Box>
  </Stack>
);

export default PrivacyDeclarationDisplayGroup;
