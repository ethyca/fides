/**
 * A component for choosing a role, meant to be embedded in a Formik form
 */
import {
  AntButton,
  Flex,
  GreenCheckCircleIcon,
  Stack,
  Text,
  useDisclosure,
} from "fidesui";
import { useFormikContext } from "formik";
import React from "react";

import { RoleRegistryEnum, System } from "~/types/api";

import QuestionTooltip from "../common/QuestionTooltip";
import AssignSystemsModal from "./AssignSystemsModal";
import { AssignSystemsDeleteTable } from "./AssignSystemsTable";
import { type FormValues } from "./PermissionsForm";

interface Props {
  label: string;
  roleKey: RoleRegistryEnum;
  isSelected: boolean;
  isDisabled: boolean;
  assignedSystems: System[];
  onAssignedSystemChange: (systems: System[]) => void;
}

const RoleOption = ({
  label,
  roleKey,
  isSelected,
  isDisabled,
  assignedSystems,
  onAssignedSystemChange,
}: Props) => {
  const { setFieldValue } = useFormikContext<FormValues>();
  const assignSystemsModal = useDisclosure();

  const handleRoleChange = () => {
    setFieldValue("roles", [roleKey]);
  };

  const buttonTitle = isDisabled
    ? "You do not have sufficient permissions to assign this role."
    : undefined;

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
        data-testid="selected"
      >
        <Flex alignItems="center" justifyContent="space-between">
          <Text fontSize="md" fontWeight="semibold">
            {label}
          </Text>
          <GreenCheckCircleIcon />
        </Flex>
        {/* The approver role cannot be assigned systems */}
        {roleKey !== RoleRegistryEnum.APPROVER ? (
          <>
            <Flex alignItems="center">
              <Text fontSize="sm" fontWeight="semibold" mr={1}>
                Assigned systems
              </Text>
              <QuestionTooltip label="Assigned systems refer to those systems that have been specifically allocated to a user for management purposes. Users assigned to a system possess full edit permissions and are listed as the Data Steward for the respective system." />
            </Flex>
            <AntButton
              disabled={isDisabled}
              title={buttonTitle}
              type="primary"
              size="small"
              onClick={assignSystemsModal.onOpen}
              data-testid="assign-systems-btn"
            >
              Assign systems +
            </AntButton>
            <AssignSystemsDeleteTable
              assignedSystems={assignedSystems}
              onAssignedSystemChange={onAssignedSystemChange}
            />
            {/* By conditionally rendering the modal, we force it to reset its state
                whenever it opens */}
            {assignSystemsModal.isOpen ? (
              <AssignSystemsModal
                isOpen={assignSystemsModal.isOpen}
                onClose={assignSystemsModal.onClose}
                assignedSystems={assignedSystems}
                onAssignedSystemChange={onAssignedSystemChange}
              />
            ) : null}
          </>
        ) : null}
      </Stack>
    );
  }

  return (
    <AntButton
      onClick={handleRoleChange}
      data-testid={`role-option-${label}`}
      title={buttonTitle}
      disabled={isDisabled}
    >
      {label}
    </AntButton>
  );
};

export default RoleOption;
