import { Alert, Flex, Tag } from "fidesui";

import type { MockSystem } from "../types";

interface SystemDetailAlertsProps {
  system: MockSystem;
}

const SystemDetailAlerts = ({ system }: SystemDetailAlertsProps) => {
  const violations = system.relationships.filter((r) => r.hasViolation);
  const { risks } = system;

  if (violations.length === 0 && risks.length === 0) {
    return null;
  }

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
      {risks.length > 0 && (
        <Alert
          type="warning"
          showIcon
          message={
            <Flex gap="small" align="center" wrap>
              <span>
                {risks.length} open risk{risks.length > 1 ? "s" : ""}
              </span>
              {risks.map((risk) => (
                <Tag key={risk.id} color="warning" bordered={false}>
                  {risk.title}
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
