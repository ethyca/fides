/**
 * A component for choosing a role, meant to be embedded in an antd Form
 */
import { Button, Card, Flex, FormInstance, Icons, Typography } from "fidesui";
import React, { useState } from "react";

import { RoleRegistryEnum, System } from "~/types/api";

import { InfoTooltip } from "../common/InfoTooltip";
import AssignSystemsModal from "./AssignSystemsModal";
import { AssignSystemsDeleteTable } from "./AssignSystemsTable";
import { type FormValues } from "./PermissionsForm";

const { Text } = Typography;

interface Props {
  label: string;
  roleKey: RoleRegistryEnum;
  isSelected: boolean;
  isDisabled: boolean;
  assignedSystems: System[];
  onAssignedSystemChange: (systems: System[]) => void;
  form: FormInstance<FormValues>;
}

const RoleOption = ({
  label,
  roleKey,
  isSelected,
  isDisabled,
  assignedSystems,
  onAssignedSystemChange,
  form,
}: Props) => {
  const [assignSystemsModalOpen, setAssignSystemsModalOpen] = useState(false);

  const handleRoleChange = () => {
    form.setFieldValue("roles", [roleKey]);
  };

  const buttonTitle = isDisabled
    ? "You do not have sufficient permissions to assign this role."
    : undefined;

  if (isSelected) {
    return (
      <Card
        size="small"
        style={{
          borderColor: "var(--ant-color-border)",
          backgroundColor: "var(--ant-color-bg-layout)",
        }}
        aria-selected="true"
        data-testid="selected"
      >
        <Flex vertical gap={16}>
          <Flex align="center" justify="space-between">
            <Text className="text-base font-semibold">{label}</Text>
            <Icons.CheckmarkFilled color="var(--fidesui-success)" />
          </Flex>
          {/* The approver and respondent roles cannot be assigned systems */}
          {roleKey !== RoleRegistryEnum.APPROVER &&
          roleKey !== RoleRegistryEnum.RESPONDENT &&
          roleKey !== RoleRegistryEnum.EXTERNAL_RESPONDENT ? (
            <>
              <Flex align="center">
                <Text className="mr-1 text-sm font-semibold">
                  Assigned systems
                </Text>
                <InfoTooltip label="Assigned systems refer to those systems that have been specifically allocated to a user for management purposes. Users assigned to a system possess full edit permissions and are listed as the Data Steward for the respective system." />
              </Flex>
              <Button
                disabled={isDisabled}
                title={buttonTitle}
                type="primary"
                size="small"
                onClick={() => setAssignSystemsModalOpen(true)}
                data-testid="assign-systems-btn"
              >
                Assign systems +
              </Button>
              <AssignSystemsDeleteTable
                assignedSystems={assignedSystems}
                onAssignedSystemChange={onAssignedSystemChange}
              />
              {/* By conditionally rendering the modal, we force it to reset its state
                  whenever it opens */}
              {assignSystemsModalOpen ? (
                <AssignSystemsModal
                  isOpen={assignSystemsModalOpen}
                  onClose={() => setAssignSystemsModalOpen(false)}
                  assignedSystems={assignedSystems}
                  onAssignedSystemChange={onAssignedSystemChange}
                />
              ) : null}
            </>
          ) : null}
        </Flex>
      </Card>
    );
  }

  return (
    <Button
      onClick={handleRoleChange}
      data-testid={`role-option-${label}`}
      title={buttonTitle}
      disabled={isDisabled}
    >
      {label}
    </Button>
  );
};

export default RoleOption;
