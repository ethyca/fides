import { useMemo } from "react";
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

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

import {
  EvaluateDecision,
  EvaluateResponse,
  PolicyViolation,
} from "./types";

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

interface DataUseGroup {
  dataUse: string;
  decision: EvaluateDecision;
  violations: PolicyViolation[];
  systems: Array<{
    systemName: string;
    systemKey: string;
    declarationName: string;
    decision: EvaluateDecision;
  }>;
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

const groupByDataUse = (results: EvaluateResponse): DataUseGroup[] => {
  const groupMap = new Map<string, DataUseGroup>();

  results.systems.forEach((system) => {
    system.declarations_evaluated.forEach((decl) => {
      let group = groupMap.get(decl.data_use);
      if (!group) {
        group = {
          dataUse: decl.data_use,
          decision: "ALLOW",
          violations: [],
          systems: [],
        };
        groupMap.set(decl.data_use, group);
      }

      group.systems.push({
        systemName: system.system_name,
        systemKey: system.system_fides_key,
        declarationName: decl.declaration_name || "Unnamed",
        decision: decl.decision,
      });

      if (decl.decision === "DENY") {
        group.decision = "DENY";
      }
    });

    // Collect violations matching each data use
    system.violations.forEach((v) => {
      if (v.data_use) {
        const group = groupMap.get(v.data_use);
        if (group) {
          group.violations.push(v);
        }
      }
    });
  });

  return Array.from(groupMap.values());
};

const DataUseResultPanel = ({ group }: { group: DataUseGroup }) => {
  const columns = [
    {
      title: "System",
      dataIndex: "systemName",
      key: "systemName",
    },
    {
      title: "Declaration",
      dataIndex: "declarationName",
      key: "declarationName",
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
      {group.violations.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ color: "#cf1322" }}>
            Violations:
          </Text>
          <ul style={{ margin: "8px 0", paddingLeft: 20 }}>
            {group.violations.map((v, i) => (
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
        dataSource={group.systems}
        columns={columns}
        rowKey={(record) => `${record.systemKey}-${record.declarationName}`}
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
  const { getDataUseDisplayName } = useTaxonomies();

  const dataUseGroups = useMemo(
    () => (results ? groupByDataUse(results) : []),
    [results],
  );

  if (!isOpen) return null;

  const title = policyName
    ? `Evaluation Results: ${policyName}`
    : "Evaluation Results: All Policies";

  const groupsWithViolations = dataUseGroups.filter(
    (g) => g.violations.length > 0,
  );
  const groupsWithoutViolations = dataUseGroups.filter(
    (g) => g.violations.length === 0,
  );

  const collapseItems: CollapseProps["items"] = [
    ...groupsWithViolations.map((group) => ({
      key: group.dataUse,
      label: (
        <Flex justify="space-between" align="center" style={{ width: "100%" }}>
          <Flex align="center" gap={8}>
            <Badge status="error" />
            {getDataUseDisplayName(group.dataUse)}
          </Flex>
          <Tag color="error">
            {group.violations.length} violation
            {group.violations.length > 1 ? "s" : ""}
          </Tag>
        </Flex>
      ),
      children: <DataUseResultPanel group={group} />,
    })),
    ...groupsWithoutViolations.map((group) => ({
      key: group.dataUse,
      label: (
        <Flex justify="space-between" align="center" style={{ width: "100%" }}>
          <Flex align="center" gap={8}>
            <Badge status="success" />
            {getDataUseDisplayName(group.dataUse)}
          </Flex>
          <Tag color="success">No violations</Tag>
        </Flex>
      ),
      children: <DataUseResultPanel group={group} />,
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
              title="Overall Status"
              value={
                results.overall_decision === "ALLOW"
                  ? "Compliant"
                  : "Non-Compliant"
              }
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
            <StatCard
              title="Data Uses Evaluated"
              value={dataUseGroups.length}
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

          {/* Data Uses accordion */}
          {collapseItems.length > 0 ? (
            <Collapse
              items={collapseItems}
              defaultActiveKey={groupsWithViolations.map((g) => g.dataUse)}
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
