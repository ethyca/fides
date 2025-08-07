import {
  AntButton as Button,
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
  Flex,
  Icons,
} from "fidesui";

import { ConditionLeaf, Operator } from "~/types/api";

const { Text } = Typography;

interface ConditionsListProps {
  conditions: ConditionLeaf[];
  onEdit: (index: number) => void;
  onDelete: (index: number) => void;
}

// Mapping for operator display labels
const operatorLabels: Record<Operator, string> = {
  [Operator.EQ]: "equals",
  [Operator.NEQ]: "not equals",
  [Operator.LT]: "less than",
  [Operator.LTE]: "less than or equal",
  [Operator.GT]: "greater than",
  [Operator.GTE]: "greater than or equal",
  [Operator.EXISTS]: "exists",
  [Operator.NOT_EXISTS]: "does not exist",
  [Operator.LIST_CONTAINS]: "list contains",
  [Operator.NOT_IN_LIST]: "not in list",
};

const ConditionsList = ({
  conditions,
  onEdit,
  onDelete,
}: ConditionsListProps) => {
  const columns = [
    {
      title: "Field Path",
      dataIndex: "field_address",
      key: "field_address",
      width: "40%",
      render: (text: string) => (
        <Text className="font-mono text-sm">{text}</Text>
      ),
    },
    {
      title: "Operator",
      dataIndex: "operator",
      key: "operator",
      width: "25%",
      render: (operator: Operator) => (
        <Tag color="blue">{operatorLabels[operator]}</Tag>
      ),
    },
    {
      title: "Value",
      dataIndex: "value",
      key: "value",
      width: "20%",
      render: (value: any) => {
        if (value === null || value === undefined) {
          return <Text type="secondary">—</Text>;
        }
        return <Text>{String(value)}</Text>;
      },
    },
    {
      title: "Actions",
      key: "actions",
      width: "15%",
      render: (_: any, record: ConditionLeaf, index: number) => (
        <Flex gap={1}>
          <Button
            size="small"
            icon={<Icons.Edit />}
            onClick={() => onEdit(index)}
            type="text"
          >
            Edit
          </Button>
          <Button
            size="small"
            danger
            icon={<Icons.TrashCan />}
            onClick={() => onDelete(index)}
            type="text"
          >
            Delete
          </Button>
        </Flex>
      ),
    },
  ];

  // Add index as key for each condition
  const dataSource = conditions.map((condition, index) => ({
    ...condition,
    key: index,
  }));

  return (
    <Table
      dataSource={dataSource}
      columns={columns}
      pagination={false}
      size="small"
      locale={{
        emptyText: (
          <div className="py-8 text-center">
            <Text type="secondary">
              No conditions configured. Manual tasks will be created for all
              privacy requests.
            </Text>
          </div>
        ),
      }}
      className="mb-4"
      bordered
    />
  );
};

export default ConditionsList;
