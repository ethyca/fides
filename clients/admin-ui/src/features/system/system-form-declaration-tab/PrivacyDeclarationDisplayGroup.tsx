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
import { useAppSelector } from "~/app/hooks";
import { selectLockedForGVL } from "~/features/system/dictionary-form/dict-suggestion.slice";

import { DataUse, PrivacyDeclarationResponse } from "~/types/api";

import { SparkleIcon } from "../../common/Icon/SparkleIcon";

const PrivacyDeclarationRow = ({
  declaration,
  title,
  handleDelete,
  handleEdit,
}: {
  declaration: PrivacyDeclarationResponse;
  title?: string;
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
            <Text>{title || declaration.data_use}</Text>
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
  headerButton,
  footerButton,
}: {
  heading: string;
  children?: React.ReactNode;
  headerButton?: React.ReactNode;
  footerButton?: React.ReactNode;
}) => (
  <Stack spacing={4}>
    <Box maxWidth="720px" border="1px" borderColor="gray.200" borderRadius={6}>
      <HStack
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
        <Spacer />
        {headerButton || null}
      </HStack>

      <Stack spacing={0}>{children}</Stack>
      <Box backgroundColor="gray.50" px={6} py={4} borderBottomRadius={6}>
        {footerButton || null}
      </Box>
    </Box>
  </Stack>
);

type Props = {
  heading: string;
  dictionaryEnabled?: boolean;
  declarations: PrivacyDeclarationResponse[];
  handleDelete: (dec: PrivacyDeclarationResponse) => void;
  handleAdd?: () => void;
  handleEdit: (dec: PrivacyDeclarationResponse) => void;
  handleOpenDictModal: () => void;
  allDataUses: DataUse[];
};

export const PrivacyDeclarationDisplayGroup = ({
  heading,
  dictionaryEnabled = false,
  declarations,
  handleAdd,
  handleDelete,
  handleEdit,
  handleOpenDictModal,
  allDataUses,
}: Props) => {
  const declarationTitle = (declaration: PrivacyDeclarationResponse) => {
    const dataUse = allDataUses.filter(
      (du) => du.fides_key === declaration.data_use
    )[0];
    if (dataUse) {
      return declaration.name
        ? `${dataUse.name} - ${declaration.name}`
        : dataUse.name;
    }
    return "";
  };

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  return (
    <PrivacyDeclarationTabTable
      heading={heading}
      headerButton={
        dictionaryEnabled ? (
          <IconButton
            onClick={handleOpenDictModal}
            aria-label="Show dictionary suggestions"
            variant="outline"
          >
            <SparkleIcon />
          </IconButton>
        ) : null
      }
      footerButton={
        !lockedForGVL ? (
          <Button
            onClick={handleAdd}
            size="xs"
            px={2}
            py={1}
            backgroundColor="primary.800"
            color="white"
            fontWeight="600"
            rightIcon={<AddIcon />}
          >
            Add data use
          </Button>
        ) : null
      }
    >
      {declarations.map((pd) => (
        <PrivacyDeclarationRow
          declaration={pd}
          key={pd.id}
          title={declarationTitle(pd)}
          handleDelete={handleDelete}
          handleEdit={handleEdit}
        />
      ))}
    </PrivacyDeclarationTabTable>
  );
};
