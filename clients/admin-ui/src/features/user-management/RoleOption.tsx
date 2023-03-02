/**
 * A component for choosing a role, meant to be embedded in a Formik form
 */
import {
  Button,
  Flex,
  GreenCheckCircleIcon,
  Stack,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";

import { RoleRegistry } from "~/types/api";

import QuestionTooltip from "../common/QuestionTooltip";
import { type FormValues } from "./PermissionsForm";

interface Props {
  label: string;
  roleKey: RoleRegistry;
  isSelected: boolean;
}

const RoleOption = ({ label, roleKey, isSelected }: Props) => {
  const { setFieldValue } = useFormikContext<FormValues>();

  const handleClick = () => {
    setFieldValue("roles", [roleKey]);
  };

  if (isSelected) {
    return (
      <Stack
        borderRadius="md"
        border="1px solid"
        borderColor="gray.200"
        p={4}
        backgroundColor="gray.50"
        aria-selected="true"
        spacing={4}
      >
        <Flex alignItems="center" justifyContent="space-between">
          <Text fontSize="md" fontWeight="semibold">
            {label}
          </Text>
          <GreenCheckCircleIcon />
        </Flex>
        <Flex alignItems="center">
          <Text fontSize="sm" fontWeight="semibold" mr={1}>
            Assigned systems
          </Text>
          <QuestionTooltip label="TODO" />
        </Flex>
        <Button colorScheme="primary" size="xs" width="fit-content">
          Assign systems +
        </Button>
      </Stack>
    );
  }

  return (
    <Button
      onClick={handleClick}
      justifyContent="start"
      variant="outline"
      height="inherit"
      p={4}
    >
      {label}
    </Button>
  );
};

export default RoleOption;
