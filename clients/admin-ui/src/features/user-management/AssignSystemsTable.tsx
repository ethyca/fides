import { Button, ColumnsType, Icons, Switch, Table } from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { System } from "~/types/api";

import {
  selectActiveUserId,
  useGetUserManagedSystemsQuery,
} from "./user-management.slice";

export const AssignSystemsDeleteTable = ({
  assignedSystems,
  onAssignedSystemChange,
}: {
  assignedSystems: System[];
  onAssignedSystemChange: (systems: System[]) => void;
}) => {
  const activeUserId = useAppSelector(selectActiveUserId);
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });

  if (assignedSystems.length === 0) {
    return null;
  }

  const onDelete = (system: System) => {
    onAssignedSystemChange(
      assignedSystems.filter(
        (assignedSystem) => assignedSystem.fides_key !== system.fides_key,
      ),
    );
  };

  const columns: ColumnsType<System> = [
    {
      title: "System",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "",
      key: "actions",
      align: "right" as const,
      render: (_, record) => (
        <Button
          aria-label="Unassign system from user"
          icon={<Icons.TrashCan />}
          onClick={() => onDelete(record)}
          data-testid="unassign-btn"
        />
      ),
    },
  ];

  return (
    <Table
      size="small"
      columns={columns}
      dataSource={assignedSystems}
      rowKey="fides_key"
      pagination={false}
      onRow={(record) =>
        ({
          "data-testid": `row-${record.fides_key}`,
        }) as React.HTMLAttributes<HTMLTableRowElement>
      }
      data-testid="assign-systems-delete-table"
    />
  );
};

const AssignSystemsTable = ({
  allSystems,
  assignedSystems,
  isLoading,
  onChange,
}: {
  allSystems: System[];
  assignedSystems: System[];
  isLoading?: boolean;
  onChange: (systems: System[]) => void;
}) => {
  const handleToggle = (system: System) => {
    const isAssigned = !!assignedSystems.find(
      (assigned) => assigned.fides_key === system.fides_key,
    );
    if (isAssigned) {
      onChange(
        assignedSystems.filter(
          (assignedSystem) => assignedSystem.fides_key !== system.fides_key,
        ),
      );
    } else {
      onChange([...assignedSystems, system]);
    }
  };

  const columns: ColumnsType<System> = [
    {
      title: "System",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Assign",
      key: "assign",
      render: (_, record) => {
        const isAssigned = !!assignedSystems.find(
          (assigned) => assigned.fides_key === record.fides_key,
        );
        return (
          <Switch
            checked={isAssigned}
            onChange={() => handleToggle(record)}
            data-testid="assign-switch"
          />
        );
      },
    },
  ];

  return (
    <div className="max-h-[300px] overflow-y-auto">
      <Table
        size="small"
        columns={columns}
        dataSource={allSystems}
        rowKey="fides_key"
        sticky
        pagination={false}
        loading={isLoading}
        onRow={(record) =>
          ({
            "data-testid": `row-${record.fides_key}`,
          }) as React.HTMLAttributes<HTMLTableRowElement>
        }
        data-testid="assign-systems-table"
      />
    </div>
  );
};

export default AssignSystemsTable;
