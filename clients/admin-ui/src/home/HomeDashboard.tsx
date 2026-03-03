import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import { Alert, Card, Col, Flex, Row, Statistic } from "fidesui";
import { RadarChart, Sparkline } from "fidesui";
import * as React from "react";
import { useEffect, useState } from "react";

import {
  useGetDashboardPostureQuery,
  useResetDashboardMutation,
} from "~/features/dashboard/dashboard.slice";

const upwardTrendData = [12, 18, 15, 22, 28, 25, 34, 30, 38, 42, 39, 47];
const downwardTrendData = [47, 42, 45, 38, 34, 36, 28, 24, 26, 18, 15, 12];
const neutralTrendData = [28, 32, 25, 30, 27, 33, 26, 31, 28, 34, 29, 30];
const steadyTrendData = [20, 22, 21, 23, 22, 24, 23, 25, 24, 26, 25, 27];

const SMALL_FONT = { fontSize: 14 };

const BAND_STATUS: Record<string, "warning" | "error" | undefined> = {
  at_risk: "warning",
  critical: "error",
};

const HomeDashboardMockup = () => {
  const [activeTab, setActiveTab] = useState("overdue");

  const [resetDashboard, { isSuccess: resetDone }] =
    useResetDashboardMutation();
  const { data: posture } = useGetDashboardPostureQuery(undefined, {
    skip: !resetDone,
  });

  useEffect(() => {
    resetDashboard();
  }, [resetDashboard]);

  const radarData = posture?.dimensions.map((d) => ({
    subject: d.label,
    value: d.score,
    status: BAND_STATUS[d.band],
  })) ?? [
    { subject: "Coverage", value: 80 },
    { subject: "Classification", value: 65 },
    { subject: "Consent", value: 50, status: "warning" as const },
    { subject: "DSR", value: 30, status: "error" as const },
    { subject: "Enforcement", value: 70 },
    { subject: "Assessments", value: 45, status: "warning" as const },
  ];

  const postureScore = posture?.score ?? 67;
  const postureDiff = posture?.diff ?? 4;
  const diffDirection = posture?.diff_direction ?? "up";

  return (
    <Flex vertical gap={24} className="px-10 pb-6 pt-6">
      {/* Middle row: Posture + Priority actions */}
      <Row gutter={24}>
        {/* Posture card */}
        <Col xs={24} md={8} lg={8} xxl={5}>
          <Card title="Posture" variant="borderless" className="h-full">
            <>
              <Statistic value={postureScore} />
              <Statistic
                trend={diffDirection === "down" ? "down" : "up"}
                value={postureDiff}
                prefix={
                  diffDirection === "down" ? (
                    <ArrowDownOutlined />
                  ) : (
                    <ArrowUpOutlined />
                  )
                }
                valueStyle={SMALL_FONT}
              />
              <div
                className="aspect-square"
                style={{ marginLeft: -12, marginRight: -12 }}
              >
                <RadarChart data={radarData} />
              </div>
              <Alert
                type="error"
                message="Helios scanned 3 systems overnight"
              />
            </>
          </Card>
        </Col>

        {/* Priority actions card with inline tabs */}
        <Col xs={24} md={16} lg={16} xxl={19}>
          <Card
            title="Priority actions"
            variant="borderless"
            className="h-full"
            headerLayout="inline"
            tabList={[
              { key: "overdue", label: "Overdue" },
              { key: "upcoming", label: "Upcoming" },
              { key: "recent", label: "Recent" },
            ]}
            activeTabKey={activeTab}
            onTabChange={setActiveTab}
            // style={{ minHeight: 340 }}
          >
            <Flex align="center" justify="center" style={{ minHeight: 200 }}>
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} content
              placeholder
            </Flex>
          </Card>
        </Col>
      </Row>

      {/* Bottom row: 4 stat cards */}
      <Row gutter={24}>
        <Col xs={24} sm={12} md={6}>
          <Card
            variant="borderless"
            title="Data sharing"
            className="overflow-clip h-full"
            cover={
              <div className="h-16">
                <Sparkline data={upwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="15,112,893" />
            <Statistic
              trend="up"
              value="112,893"
              prefix={<ArrowUpOutlined />}
              valueStyle={SMALL_FONT}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            variant="borderless"
            title="Active users"
            className="overflow-clip h-full"
            cover={
              <div className="h-16">
                <Sparkline data={downwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="8,430" />
            <Statistic
              trend="down"
              value="1,204"
              prefix={<ArrowDownOutlined />}
              valueStyle={SMALL_FONT}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            variant="borderless"
            title="Total requests"
            className="overflow-clip h-full"
            cover={
              <div className="h-16">
                <Sparkline data={neutralTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="3,201,554" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            variant="borderless"
            title="Consent rate"
            className="overflow-clip h-full"
            cover={
              <div className="h-16">
                <Sparkline data={steadyTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="74.2%" />
            <Statistic
              trend="up"
              value="2.1%"
              prefix={<ArrowUpOutlined />}
              valueStyle={SMALL_FONT}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={24}>
        <Col xs={24} sm={12} md={7}>
          <Card
            variant="borderless"
            title="System Health"
            className="overflow-clip h-full"
          ></Card>
        </Col>
        <Col xs={24} sm={12} md={17}>
          <Card
            variant="borderless"
            title="DSR Timeline"
            className="overflow-clip h-full"
          ></Card>
        </Col>
      </Row>
    </Flex>
  );
};

export default HomeDashboardMockup;
