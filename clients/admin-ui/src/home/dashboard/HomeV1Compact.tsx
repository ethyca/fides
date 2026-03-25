/**
 * Home 1 — "Compact Executive"
 *
 * Tightest layout. Progress circle instead of radar. Everything compressed.
 */
import { Col, Flex, Row } from "fidesui";
import type { ReactNode } from "react";

import AlertBanner from "./components/AlertBanner";
import DsrStatus from "./components/DsrStatus";
import GovernancePosture from "./components/GovernancePosture";
import PriorityActions from "./components/PriorityActions";
import SparklineMetricCard from "./components/SparklineMetricCard";
import StatusStrip from "./components/StatusStrip";
import SystemCoverage from "./components/SystemCoverage";
import {
  MOCK_ALERT,
  MOCK_DSR_STATUS,
  MOCK_GOVERNANCE,
  MOCK_PRIORITY_ACTIONS,
  MOCK_SPARKLINE_CARDS,
  MOCK_SUMMARY,
  MOCK_SYSTEM_COVERAGE,
} from "./mockData";

interface HomeV1CompactProps {
  themeToggle?: ReactNode;
}

const HomeV1Compact = ({ themeToggle }: HomeV1CompactProps) => (
  <Flex vertical gap={16}>
    {/* Status strip */}
    <StatusStrip data={MOCK_SUMMARY} trailing={themeToggle} />

    {/* Alert banner */}
    <AlertBanner data={MOCK_ALERT} />

    {/* Governance + Priority Actions: 1/4 + 3/4 */}
    <Row gutter={[16, 16]}>
      <Col xs={24} md={6}>
        <GovernancePosture data={MOCK_GOVERNANCE} variant="radar" />
      </Col>
      <Col xs={24} md={18}>
        <PriorityActions tabs={MOCK_PRIORITY_ACTIONS} />
      </Col>
    </Row>

    {/* 4 sparkline metric cards */}
    <Row gutter={[16, 16]}>
      {MOCK_SPARKLINE_CARDS.map((card) => (
        <Col key={card.title} xs={24} sm={12} xl={6}>
          <SparklineMetricCard card={card} sparklineHeight={48} />
        </Col>
      ))}
    </Row>

    {/* System Coverage + DSR Status: 50/50 */}
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12}>
        <SystemCoverage data={MOCK_SYSTEM_COVERAGE} />
      </Col>
      <Col xs={24} md={12}>
        <DsrStatus data={MOCK_DSR_STATUS} />
      </Col>
    </Row>
  </Flex>
);

export default HomeV1Compact;
