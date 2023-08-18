import { AddIcon, DeleteIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  Divider,
  Heading,
  HStack,
  IconButton,
  LinkBox,
  LinkOverlay,
  Spacer,
  Stack,
  Text,
} from "@fidesui/react";

import { PrivacyDeclarationResponse } from "~/types/api";

const PrivacyDeclarationRow = ({
  declaration,
  handleDelete,
  handleEdit,
}: {
  declaration: PrivacyDeclarationResponse;
  handleDelete: (dec: PrivacyDeclarationResponse) => void;
  handleEdit: (dec: PrivacyDeclarationResponse) => void;
}) => (
  <>
    <Box px={6} py={4}>
      <HStack>
        <LinkBox
          onClick={() => handleEdit(declaration)}
          w="100%"
          h="100%"
          cursor="pointer"
        >
          <LinkOverlay>
            <Text>
              {declaration.name ? declaration.name : declaration.data_use}
            </Text>
          </LinkOverlay>
        </LinkBox>
        <Spacer />
        <IconButton
          aria-label="delete-declaration"
          variant="outline"
          zIndex={2}
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

export const PrivacyDeclarationTabTable = ({
  heading,
  children,
  hasAddButton = false,
  handleAdd,
}: {
  heading: string;
  children?: React.ReactNode;
  hasAddButton?: boolean;
  handleAdd?: () => void;
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

      <Stack spacing={0}>{children}</Stack>
      <Box backgroundColor="gray.50" px={6} py={4} borderBottomRadius={6}>
        {hasAddButton ? (
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
        ) : null}
      </Box>
    </Box>
  </Stack>
);

export const PrivacyDeclarationDisplayGroup = ({
  heading,
  declarations,
  handleAdd,
  handleDelete,
  handleEdit,
}: {
  heading: string;
  declarations: PrivacyDeclarationResponse[];
  handleAdd?: () => void;
  handleDelete: (dec: PrivacyDeclarationResponse) => void;
  handleEdit: (dec: PrivacyDeclarationResponse) => void;
}) => (
  <PrivacyDeclarationTabTable
    heading={heading}
    hasAddButton
    handleAdd={handleAdd}
  >
    {declarations.map((pd) => (
      <PrivacyDeclarationRow
        declaration={pd}
        key={pd.id}
        handleDelete={handleDelete}
        handleEdit={handleEdit}
      />
    ))}
  </PrivacyDeclarationTabTable>
);
