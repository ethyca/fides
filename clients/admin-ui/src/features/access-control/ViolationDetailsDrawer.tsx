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
import React from "react";

import { RequestLogEntry } from "./types";

const { Text, Title } = Typography;

// Palette-based SQL colors on light (gray-50) background
const SQL_COLORS = {
  keyword: "#7b4ea9", // alert / purple
  string: "#5a9a68", // success / green
  number: "#b9704b", // terracotta
  operator: "#e59d47", // warning / orange
  default: "#2b2e35", // minos — dark text on light bg
  comment: "#7e8185", // neutral-600
};

const SQL_KEYWORDS = new Set([
  "SELECT",
  "FROM",
  "WHERE",
  "AND",
  "OR",
  "INSERT",
  "INTO",
  "UPDATE",
  "DELETE",
  "JOIN",
  "LEFT",
  "RIGHT",
  "INNER",
  "OUTER",
  "ON",
  "GROUP",
  "BY",
  "ORDER",
  "LIMIT",
  "OFFSET",
  "AS",
  "IN",
  "NOT",
  "NULL",
  "IS",
  "LIKE",
  "BETWEEN",
  "EXISTS",
  "HAVING",
  "UNION",
  "ALL",
  "DISTINCT",
  "SET",
  "VALUES",
  "CREATE",
  "DROP",
  "ALTER",
  "TABLE",
  "INDEX",
  "SAMPLE",
  "INTERVAL",
  "NOW",
]);

const highlightSQL = (sql: string): React.ReactNode[] => {
  // tokenize: strings, numbers, words, operators, whitespace/other
  const tokenRegex =
    /'[^']*'|"[^"]*"|\b\d+(?:\.\d+)?\b|[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*|\S|\s+/g;
  const tokens: React.ReactNode[] = [];
  const allMatches = Array.from(sql.matchAll(tokenRegex));

  allMatches.forEach((match, i) => {
    const token = match[0];
    const key = i;

    if (token.startsWith("'") || token.startsWith('"')) {
      tokens.push(
        <span key={key} style={{ color: SQL_COLORS.string }}>
          {token}
        </span>,
      );
    } else if (/^\d/.test(token)) {
      tokens.push(
        <span key={key} style={{ color: SQL_COLORS.number }}>
          {token}
        </span>,
      );
    } else if (SQL_KEYWORDS.has(token.toUpperCase())) {
      tokens.push(
        <span key={key} style={{ color: SQL_COLORS.keyword, fontWeight: 600 }}>
          {token}
        </span>,
      );
    } else if (/^[=<>!*+\-/();,]$/.test(token)) {
      tokens.push(
        <span key={key} style={{ color: SQL_COLORS.operator }}>
          {token}
        </span>,
      );
    } else {
      tokens.push(
        <span key={key} style={{ color: SQL_COLORS.default }}>
          {token}
        </span>,
      );
    }
  });

  return tokens;
};

interface ViolationDetailsDrawerProps {
  open: boolean;
  onClose: () => void;
  violation: RequestLogEntry | null;
}

const ViolationDetailsDrawer = ({
  open,
  onClose,
  violation,
}: ViolationDetailsDrawerProps) => {
  if (!violation) {
    return null;
  }

  const initials = violation.consumer
    .split(/[\s-]/)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const timestamp = new Date(violation.timestamp);

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
      <div className="space-y-6">
        <div>
          <Text
            className="mb-2 block text-xs font-semibold"
            style={{ color: "#2b2e35" }}
          >
            Violation reason
          </Text>
          <div className="rounded-lg bg-gray-50 p-5">
            <Text className="text-sm leading-relaxed">
              {violation.violationReason}
            </Text>
          </div>
        </div>

        <div>
          <Text
            className="mb-2 block text-xs font-semibold"
            style={{ color: "#2b2e35" }}
          >
            Data consumer
          </Text>
          <Flex justify="space-between" align="center">
            <Flex align="center" gap="middle">
              <Avatar
                size="large"
                style={{ backgroundColor: "#53575c", color: "#fff" }}
              >
                {initials}
              </Avatar>
              <div>
                <Text strong className="block">
                  {violation.consumer}
                </Text>
                <Text type="secondary" className="text-sm">
                  {violation.consumerEmail}
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
          <Text
            className="mb-2 block text-xs font-semibold"
            style={{ color: "#2b2e35" }}
          >
            Details
          </Text>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs" style={{ color: "#2b2e35" }}>
                Timestamp
              </Text>
              <Text className="text-sm">
                {timestamp.toISOString().slice(0, 10)}{" "}
                {timestamp.toISOString().slice(11, 19)}
              </Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs" style={{ color: "#2b2e35" }}>
                System
              </Text>
              <Text className="text-sm">{violation.system}</Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs" style={{ color: "#2b2e35" }}>
                Dataset
              </Text>
              <Text className="text-sm">{violation.dataset}</Text>
            </div>
            <div className="rounded-lg bg-gray-50 px-4 py-3">
              <Text className="mb-1 block text-xs" style={{ color: "#2b2e35" }}>
                Table
              </Text>
              <Text className="text-sm">{violation.table}</Text>
            </div>
          </div>
        </div>

        <div>
          <Text
            className="mb-2 block text-xs font-semibold"
            style={{ color: "#2b2e35" }}
          >
            Request context
          </Text>
          <div className="rounded-lg bg-gray-50 p-5">
            <pre className="m-0 whitespace-pre-wrap font-mono text-xs leading-relaxed">
              {highlightSQL(violation.requestContext)}
            </pre>
          </div>
        </div>

        <div>
          <Text
            className="mb-2 block text-xs font-semibold"
            style={{ color: "#2b2e35" }}
          >
            Policy deviated
          </Text>
          <div className="rounded-lg border border-gray-200 p-5">
            <Flex align="center" gap="small" className="mb-2">
              <Title level={5} className="!m-0">
                {violation.policy}
              </Title>
              <Tag color={CUSTOM_TAG_COLOR.SANDSTONE}>
                {violation.controlName}
              </Tag>
            </Flex>
            <Text type="secondary" className="block text-sm leading-relaxed">
              {violation.policyDescription}
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
    </Drawer>
  );
};

export default ViolationDetailsDrawer;
