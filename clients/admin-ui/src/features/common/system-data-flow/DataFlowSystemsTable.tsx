import { Switch, Table, Text } from "fidesui";
import React from "react";

import { DataFlow, System } from "~/types/api";

type Props = {
  allSystems: System[];
  dataFlowSystems: DataFlow[];
  onChange: (dataFlows: DataFlow[]) => void;
  flowType: string;
};

const DataFlowSystemsTable = ({
  allSystems,
  dataFlowSystems,
  onChange,
  flowType,
}: Props) => {
  const handleToggle = (system: System) => {
    const isAssigned = !!dataFlowSystems.find(
      (assigned) => assigned.fides_key === system.fides_key,
    );
    if (isAssigned) {
      onChange(
        dataFlowSystems.filter(
          (assignedSystem) => assignedSystem.fides_key !== system.fides_key,
        ),
      );
    } else {
      onChange([
        ...dataFlowSystems,
        { fides_key: system.fides_key, type: "system" },
      ]);
    }
  };

  return (
    <div className="max-h-[300px] overflow-y-auto">
      <Table
        size="small"
        dataSource={allSystems}
        rowKey="fides_key"
        pagination={false}
        data-testid="assign-systems-table"
        columns={[
          {
            title: "System",
            dataIndex: "name",
            render: (name: string) => (
              <Text className="text-xs font-medium leading-4">{name}</Text>
            ),
          },
          {
            title: `Set as ${flowType}`,
            key: "toggle",
            align: "right" as const,
            render: (_: unknown, system: System) => {
              const isAssigned = !!dataFlowSystems.find(
                (assigned) => assigned.fides_key === system.fides_key,
              );
              return (
                <Switch
                  checked={isAssigned}
                  onChange={() => handleToggle(system)}
                  data-testid="assign-switch"
                />
              );
            },
          },
        ]}
      />
    </div>
  );
};

export default DataFlowSystemsTable;
