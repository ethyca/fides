import {
  Avatar,
  Button,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Icons,
  Tag,
  Typography,
} from "fidesui";
import type { ReactNode } from "react";

import { useGetViolationDetailQuery } from "../access-control.slice";

const { Text, Title } = Typography;

const SQL_COLORS = {
  keyword: "text-[#7b4ea9]",
  string: "text-[#5a9a68]",
  number: "text-[#b9704b]",
  operator: "text-[#e59d47]",
  default: "text-neutral-10",
};

const SQL_KEYWORDS = new Set([
  "SELECT", "FROM", "WHERE", "AND", "OR", "INSERT", "INTO", "UPDATE",
  "DELETE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "GROUP",
  "BY", "ORDER", "LIMIT", "OFFSET", "AS", "IN", "NOT", "NULL", "IS",
  "LIKE", "BETWEEN", "EXISTS", "HAVING", "UNION", "ALL", "DISTINCT",
  "SET", "VALUES", "CREATE", "DROP", "ALTER", "TABLE", "INDEX",
  "SAMPLE", "INTERVAL", "NOW",
]);

const highlightSQL = (sql: string): ReactNode[] => {
  const tokenRegex =
    /'[^']*'|"[^"]*"|\b\d+(?:\.\d+)?\b|[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*|\S|\s+/g;
  const tokens: ReactNode[] = [];

  Array.from(sql.matchAll(tokenRegex)).forEach((match, i) => {
    const token = match[0];
    if (token.startsWith("'") || token.startsWith('"')) {
      tokens.push(<span key={i} className={SQL_COLORS.string}>{token}</span>);
    } else if (/^\d/.test(token)) {
      tokens.push(<span key={i} className={SQL_COLORS.number}>{token}</span>);
    } else if (SQL_KEYWORDS.has(token.toUpperCase())) {
      tokens.push(<span key={i} className={`${SQL_COLORS.keyword} font-semibold`}>{token}</span>);
    } else if (/^[=<>!*+\-/();,]$/.test(token)) {
      tokens.push(<span key={i} className={SQL_COLORS.operator}>{token}</span>);
    } else {
      tokens.push(<span key={i} className={SQL_COLORS.default}>{token}</span>);
    }
  });

  return tokens;
};

interface ViolationDetailDrawerProps {
  violationId: string | null;
  open: boolean;
  onClose: () => void;
}

export const ViolationDetailDrawer = ({
  violationId,
  open,
  onClose,
}: ViolationDetailDrawerProps) => {
  const { data: violation } = useGetViolationDetailQuery(violationId!, {
    skip: !violationId,
  });

  const initials = violation
    ? violation.consumer
        .split(/[\s-]/)
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "";

  const timestamp = violation ? new Date(violation.timestamp) : null;

  return (
    <Drawer
      title="Violation details"
      placement="right"
      onClose={onClose}
      open={open}
      width={480}
      footer={
        <Flex gap="small" justify="flex-end">
          <Button>Edit policy</Button>
          <Button type="primary">Create new policy</Button>
        </Flex>
      }
    >
      {violation && timestamp && (
      <div className="space-y-6">
        <div>
          <Text className="mb-2 block text-xs font-semibold text-neutral-10">
            Violation reason
          </Text>
          <div className="rounded-lg bg-gray-50 p-5">
            <Text className="text-sm leading-relaxed">
              {violation.ai_reason ?? "Analysis pending..."}
            </Text>
          </div>
        </div>

        <div>
          <Text className="mb-2 block text-xs font-semibold text-neutral-10">
            Data consumer
          </Text>
          <Flex justify="space-between" align="center">
            <Flex align="center" gap="middle">
              <Avatar
                size="large"
                className="!bg-neutral-9 !text-white"
              >
                {initials}
              </Avatar>
              <div>
                <Text strong className="block">
                  {violation.consumer}
                </Text>
                <Text type="secondary" className="text-sm">
                  {violation.consumer_email}
                </Text>
              </div>
            </Flex>
            <Button
              size="small"
              icon={<Icons.LogoSlack size={14} />}
              type="text"
            >
              Slack
            </Button>
          </Flex>
        </div>

        <div>
          <Text className="mb-2 block text-xs font-semibold text-neutral-10">
            Details
          </Text>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs text-neutral-10">
                Timestamp
              </Text>
              <Text className="text-sm">
                {timestamp.toISOString().slice(0, 10)}{" "}
                {timestamp.toISOString().slice(11, 19)}
              </Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs text-neutral-10">
                Data use
              </Text>
              <Text className="text-sm">{violation.data_use}</Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs text-neutral-10">
                Dataset
              </Text>
              <Text className="text-sm">{violation.dataset}</Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs text-neutral-10">
                Policy
              </Text>
              <Text className="text-sm">{violation.policy}</Text>
            </div>
          </div>
        </div>

        <div>
          <Text className="mb-2 block text-xs font-semibold text-neutral-10">
            Request context
          </Text>
          <div className="rounded-lg bg-gray-50 p-5">
            <pre className="m-0 whitespace-pre-wrap font-mono text-xs leading-relaxed">
              {highlightSQL(violation.sql_statement)}
            </pre>
          </div>
        </div>

        <div>
          <Text className="mb-2 block text-xs font-semibold text-neutral-10">
            Policy deviated
          </Text>
          <div className="rounded-lg border border-gray-200 p-5">
            <Flex align="center" gap="small" className="mb-2">
              <Title level={5} className="!m-0">
                {violation.policy}
              </Title>
              <Tag color={CUSTOM_TAG_COLOR.SANDSTONE}>
                {violation.data_use}
              </Tag>
            </Flex>
            <Text type="secondary" className="block text-sm leading-relaxed">
              {violation.policy_description}
            </Text>
            <Flex align="center" gap={4} className="mt-3">
              <Text type="secondary" className="text-sm font-medium">
                View policy
              </Text>
              <Icons.ArrowRight size={14} />
            </Flex>
          </div>
        </div>
      </div>
      )}
    </Drawer>
  );
};
