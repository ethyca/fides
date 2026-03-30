import { Alert, Flex, Tag } from "fidesui";

import type { MockSystem } from "../types";

interface SystemDetailAlertsProps {
  system: MockSystem;
}

const SystemDetailAlerts = ({ system }: SystemDetailAlertsProps) => {
  const violations = system.relationships.filter((r) => r.hasViolation);
  const issues = system.issues;

  if (violations.length === 0 && issues.length === 0) return null;

  return (
    <Flex vertical gap="small" className="mb-4">
      {violations.length > 0 && (
        <Alert
          type="error"
          showIcon
          message={
            <Flex gap="small" align="center" wrap>
              <span>
                {violations.length} policy violation
                {violations.length > 1 ? "s" : ""}
              </span>
              {violations.map((v) => (
                <Tag key={v.systemKey} color="error" bordered={false}>
                  {v.violationReason ?? "Purpose mismatch"}
                </Tag>
              ))}
            </Flex>
          }
        />
      )}
      {issues.length > 0 && (
        <Alert
          type="warning"
          showIcon
          message={
            <Flex gap="small" align="center" wrap>
              <span>
                {issues.length} governance issue{issues.length > 1 ? "s" : ""}
              </span>
              {issues.map((issue) => (
                <Tag key={issue.title} color="warning" bordered={false}>
                  {issue.title}
                </Tag>
              ))}
            </Flex>
          }
        />
      )}
    </Flex>
  );
};

export default SystemDetailAlerts;
