import { Button, Icons, Table, Text } from "fidesui";
import React from "react";

import { DataFlow, System } from "~/types/api";

type Props = {
  systems: System[];
  dataFlows: DataFlow[];
  onDelete: (system: System) => void;
};

export const DataFlowSystemsDeleteTable = ({
  systems,
  dataFlows,
  onDelete,
}: Props) => {
  const dataFlowKeys = dataFlows.map((f) => f.fides_key);
  const dataSource = systems.filter((system) =>
    dataFlowKeys.includes(system.fides_key),
  );

  return (
    <Table
      size="small"
      dataSource={dataSource}
      rowKey="fides_key"
      pagination={false}
      data-testid="assign-systems-delete-table"
      columns={[
        {
          title: "System",
          dataIndex: "name",
          render: (name: string) => (
            <Text className="text-xs font-medium leading-4">{name}</Text>
          ),
        },
        {
          title: "",
          key: "actions",
          align: "right" as const,
          render: (_: unknown, system: System) => (
            <Button
              aria-label="Unassign data flow from system"
              icon={<Icons.TrashCan />}
              onClick={() => onDelete(system)}
              data-testid="unassign-btn"
            />
          ),
        },
      ]}
    />
  );
};
