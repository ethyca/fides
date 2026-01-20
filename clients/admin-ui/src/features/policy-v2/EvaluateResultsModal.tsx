import {
  Badge,
  Collapse,
  CollapseProps,
  Flex,
  Modal,
  Spin,
  Table,
  Tag,
  Typography,
} from "fidesui";

import { EvaluateResponse, SystemEvaluationResult } from "./types";

const { Text, Title } = Typography;

interface EvaluateResultsModalProps {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  results: EvaluateResponse | null;
  policyName?: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  color?: string;
}

const StatCard = ({ title, value, color }: StatCardProps) => (
  <Flex
    vertical
    align="center"
    style={{
      padding: "16px 24px",
      background: "#fafafa",
      borderRadius: 8,
      minWidth: 120,
    }}
  >
    <Text type="secondary" style={{ fontSize: 12 }}>
      {title}
    </Text>
    <Title level={3} style={{ margin: 0, color: color || "inherit" }}>
      {value}
    </Title>
  </Flex>
);

const SystemResultPanel = ({ system }: { system: SystemEvaluationResult }) => {
  const columns = [
    {
      title: "Declaration",
      dataIndex: "declaration_name",
      key: "declaration_name",
      render: (name: string | undefined) => name || "Unnamed",
    },
    {
      title: "Data Use",
      dataIndex: "data_use",
      key: "data_use",
      render: (dataUse: string) => <Tag color="default">{dataUse}</Tag>,
    },
    {
      title: "Decision",
      dataIndex: "decision",
      key: "decision",
      render: (decision: string) => (
        <Tag color={decision === "ALLOW" ? "success" : "error"}>{decision}</Tag>
      ),
    },
  ];

  return (
    <div>
      {system.violations.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ color: "#cf1322" }}>
            Violations:
          </Text>
          <ul style={{ margin: "8px 0", paddingLeft: 20 }}>
            {system.violations.map((v, i) => (
              <li key={i} style={{ marginBottom: 4 }}>
                <Text type="danger">
                  {v.message} ({v.declaration_name || v.data_use})
                </Text>
              </li>
            ))}
          </ul>
        </div>
      )}
      <Table
        dataSource={system.declarations_evaluated}
        columns={columns}
        rowKey={(record) => `${record.declaration_name}-${record.data_use}`}
        size="small"
        pagination={false}
      />
    </div>
  );
};

export const EvaluateResultsModal = ({
  isOpen,
  onClose,
  isLoading,
  results,
  policyName,
}: EvaluateResultsModalProps) => {
  if (!isOpen) return null;

  const title = policyName
    ? `Evaluation Results: ${policyName}`
    : "Evaluation Results: All Policies";

  // Build collapse items for systems with violations first, then others
  const systemsWithViolations =
    results?.systems.filter((s) => s.violations.length > 0) || [];
  const systemsWithoutViolations =
    results?.systems.filter((s) => s.violations.length === 0) || [];

  const collapseItems: CollapseProps["items"] = [
    ...systemsWithViolations.map((system) => ({
      key: system.system_fides_key,
      label: (
        <Flex justify="space-between" align="center" style={{ width: "100%" }}>
          <span>
            <Badge status="error" />
            {system.system_name}
          </span>
          <Tag color="error">
            {system.violations.length} violation
            {system.violations.length > 1 ? "s" : ""}
          </Tag>
        </Flex>
      ),
      children: <SystemResultPanel system={system} />,
    })),
    ...systemsWithoutViolations.map((system) => ({
      key: system.system_fides_key,
      label: (
        <Flex justify="space-between" align="center" style={{ width: "100%" }}>
          <span>
            <Badge status="success" />
            {system.system_name}
          </span>
          <Tag color="success">No violations</Tag>
        </Flex>
      ),
      children: <SystemResultPanel system={system} />,
    })),
  ];

  return (
    <Modal
      title={title}
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={800}
      styles={{ body: { maxHeight: "70vh", overflowY: "auto" } }}
    >
      {isLoading ? (
        <Flex justify="center" align="center" style={{ padding: 40 }}>
          <Spin size="large" />
        </Flex>
      ) : results ? (
        <Flex vertical gap="middle">
          {/* Summary statistics */}
          <Flex gap="large" justify="space-around">
            <StatCard
              title="Overall Decision"
              value={results.overall_decision}
              color={
                results.overall_decision === "ALLOW" ? "#3f8600" : "#cf1322"
              }
            />
            <StatCard
              title="Systems Evaluated"
              value={results.total_systems_evaluated}
            />
            <StatCard
              title="Total Violations"
              value={results.total_violations}
              color={results.total_violations > 0 ? "#cf1322" : "#3f8600"}
            />
          </Flex>

          {/* Warnings */}
          {results.warnings.length > 0 && (
            <div>
              <Text type="warning">Warnings:</Text>
              <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                {results.warnings.map((w, i) => (
                  <li key={i}>
                    <Text type="warning">{w}</Text>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Systems accordion */}
          {collapseItems.length > 0 ? (
            <Collapse
              items={collapseItems}
              defaultActiveKey={systemsWithViolations.map(
                (s) => s.system_fides_key
              )}
              size="small"
            />
          ) : (
            <Text type="secondary">No systems found to evaluate.</Text>
          )}
        </Flex>
      ) : (
        <Text type="secondary">No results available.</Text>
      )}
    </Modal>
  );
};
