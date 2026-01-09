import {
  Avatar,
  Button,
  Card,
  Collapse,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Form,
  Input,
  Select,
  Space,
  Steps,
  Tag,
  Typography,
  CheckOutlined,
  PlusOutlined,
} from "fidesui";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import {
  SearchOutlined,
  InfoCircleOutlined,
  LockOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  GlobalOutlined,
  ThunderboltOutlined,
  CloseOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import type { NextPage } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const { Title, Text } = Typography;
const { Panel } = Collapse;

interface ChatMessage {
  id: string;
  sender: "astralis" | "jack";
  senderName: string;
  message: string;
  timestamp: string;
}

const PrivacyAssessmentDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Mock Slack conversation data
  const chatMessages: ChatMessage[] = [
    {
      id: "1",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "I've analyzed the Customer Insight AI Module and identified 2 data categories: PII and Behavioral Data. The processing involves automated AI analysis for personalized recommendations.",
      timestamp: "2:15 PM",
    },
    {
      id: "2",
      sender: "jack",
      senderName: "Jack Gale",
      message: "Thanks! Can you help me understand the data flow? How is the data ingested?",
      timestamp: "2:18 PM",
    },
    {
      id: "3",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "Based on the system architecture, data is ingested via API from the core commerce engine. It's processed in a secure isolated environment with machine learning algorithms analyzing purchase history and browsing behavior.",
      timestamp: "2:19 PM",
    },
    {
      id: "4",
      sender: "jack",
      senderName: "Jack Gale",
      message: "What about the retention period? Do we have that information?",
      timestamp: "2:22 PM",
    },
    {
      id: "5",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "The retention period is 24 months based on the legitimate interest lawful basis. This aligns with the marketing communication opt-in period for customers.",
      timestamp: "2:23 PM",
    },
    {
      id: "6",
      sender: "jack",
      senderName: "Jack Gale",
      message: "Perfect, that helps. I'll update the assessment with this information.",
      timestamp: "2:25 PM",
    },
  ];

  const handleExpandAll = () => {
    setExpandedKeys(["1", "2", "3", "4", "5"]);
  };

  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  const steps = [
    {
      title: "Description",
      status: "finish",
    },
    {
      title: "Necessity",
      status: "finish",
    },
    {
      title: "Risks",
      status: "process",
    },
    {
      title: "Measures",
      status: "wait",
    },
    {
      title: "Review",
      status: "wait",
    },
  ];

  return (
    <Layout title="Privacy assessments">
      <Head>
        <style>{`
          .privacy-assessment-collapse .ant-collapse-item {
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            margin-bottom: 0;
            overflow: hidden;
            position: relative;
            transition: border-color 0.2s ease;
          }
          .privacy-assessment-collapse .ant-collapse-item:not(:last-child) {
            border-bottom: 1px solid #f0f0f0;
            margin-bottom: 0;
          }
          .privacy-assessment-collapse .ant-collapse-item:not(:first-child) {
            border-top: 1px solid #f0f0f0;
          }
          .privacy-assessment-collapse .ant-collapse-item-active {
            border-left: 6px solid ${palette.FIDESUI_MINOS} !important;
          }
          .privacy-assessment-collapse .ant-collapse-header {
            display: flex;
            align-items: center;
            min-height: 80px;
            padding: 16px 24px 16px 24px !important;
            padding-right: 140px !important;
            position: relative;
            transition: min-height 1.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
            min-height: 60px;
          }
          .privacy-assessment-collapse .ant-collapse-arrow {
            position: absolute;
            top: 50%;
            left: 24px;
            transform: translateY(-50%);
            margin-top: 0 !important;
            display: flex;
            align-items: center;
            justify-content: center;
            height: auto;
            padding: 0 8px;
            transition: transform 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1;
          }
          .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-arrow {
            transform: translateY(-50%) rotate(90deg);
          }
          .privacy-assessment-collapse .ant-collapse-arrow svg {
            margin: 0;
            transition: transform 1.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .privacy-assessment-collapse .ant-collapse-header-text {
            margin-left: 40px;
            margin-right: 0;
            width: calc(100% - 40px);
            transition: opacity 0.6s ease;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-header-text > div {
            max-width: 100%;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-content {
            transition: height 1.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.8s ease;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-content-box {
            padding-top: 0;
            transition: padding 1.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .privacy-assessment-collapse .ant-collapse-header-text .ant-tag {
            position: static !important;
            display: inline;
            margin-left: 4px;
          }
          .privacy-assessment-collapse .status-tag-container {
            position: absolute;
            right: 24px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 2;
          }
        `}</style>
      </Head>
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          { title: "Privacy assessments" },
        ]}
        rightContent={
          <Space>
            <Button>Save as draft</Button>
            <Button type="primary">Generate report</Button>
          </Space>
        }
      />
      <div style={{ padding: "24px 40px" }}>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Steps
            current={2}
            size="small"
            items={steps.map((step, index) => ({
              title: step.title,
              status: step.status as any,
            }))}
            style={{ marginBottom: 32 }}
          />

          <Flex justify="space-between" align="center" style={{ marginTop: 16 }}>
            <Input
              placeholder="Search risks, authors, or content"
              prefix={<SearchOutlined />}
              suffix={
                <Tag color={CUSTOM_TAG_COLOR.MARBLE}>
                  /
                </Tag>
              }
              style={{ flex: 1, maxWidth: 400 }}
            />
            <Flex gap="small">
              <Button type="link" onClick={handleExpandAll}>
                Expand all
              </Button>
              <Button type="link" onClick={handleCollapseAll}>
                Collapse all
              </Button>
            </Flex>
          </Flex>

          <Collapse
            activeKey={expandedKeys}
            onChange={(keys) => setExpandedKeys(keys as string[])}
            className="privacy-assessment-collapse"
            style={{
              backgroundColor: "white",
              border: "1px solid #f0f0f0",
              borderRadius: 8,
            }}
          >
            <Panel
              header={
                <>
                  {expandedKeys.includes("1") ? (
                    <Text strong style={{ fontSize: 16 }}>Description of the processing</Text>
                  ) : (
                    <Flex gap="large" align="center" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ minWidth: 60, flexShrink: 0 }}>
                        <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
                          Step
                        </Text>
                        <Text strong style={{ fontSize: 20, display: "block", lineHeight: 1 }}>
                          1
                        </Text>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 8, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            Description of the processing
                          </Text>
                        </Flex>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Updated 2m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                          </Text>
                        </div>
                        <Flex gap="large" wrap="wrap">
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            <Text strong>Fields:</Text> 5/5
                          </Text>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: palette.FIDESUI_SUCCESS,
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>Risk Level:</Text> Low
                            </Text>
                          </Flex>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: palette.FIDESUI_SUCCESS,
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>AI Confidence:</Text> High
                            </Text>
                          </Flex>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                  </div>
                </>
              }
              key="1"
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <Card
                  title="PROCESSING OVERVIEW"
                  style={{ marginBottom: 24 }}
                >
                  <Flex gap="large" style={{ marginBottom: 24 }}>
                    <Card
                      style={{
                        flex: 1,
                        border: "1px solid #f0f0f0",
                        borderRadius: 8,
                        padding: 16,
                      }}
                      bodyStyle={{ padding: 0 }}
                    >
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        SCOPE
                      </Text>
                      <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
                        2 Categories Identified
                      </Text>
                      <Space size="small">
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral Data</Tag>
                      </Space>
                    </Card>
                    <Card
                      style={{
                        flex: 1,
                        border: "1px solid #f0f0f0",
                        borderRadius: 8,
                        padding: 16,
                      }}
                      bodyStyle={{ padding: 0 }}
                    >
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        NATURE
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <ThunderboltOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>AI Analysis</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Automated Processing
                      </Text>
                    </Card>
                    <Card
                      style={{
                        flex: 1,
                        border: "1px solid #f0f0f0",
                        borderRadius: 8,
                        padding: 16,
                      }}
                      bodyStyle={{ padding: 0 }}
                    >
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        CONTEXT
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <GlobalOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>External</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Customer Facing
                      </Text>
                    </Card>
                  </Flex>
                  <Flex justify="space-between" align="center">
                    <Flex align="center" gap="small">
                      <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 14 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Request sent 2h ago to @DataSteward
                      </Text>
                    </Flex>
                    <Space>
                      <Button icon={<MessageOutlined />}>
                        Request information from team
                      </Button>
                      <Button type="default" onClick={() => setIsDrawerOpen(true)}>
                        View AI Context
                      </Button>
                    </Space>
                  </Flex>
                </Card>

                <Form layout="vertical">
                  <Space direction="vertical" size="large" style={{ width: "100%" }}>
                    <Flex gap="middle" align="flex-start">
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Project name</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          </Flex>
                        }
                        name="projectName"
                        initialValue="Customer Insight AI Module"
                        style={{ flex: 1 }}
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Assessment Framework</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          </Flex>
                        }
                        name="framework"
                        initialValue="GDPR-DPIA"
                        style={{ flex: 1 }}
                      >
                        <Select
                          options={[
                            { value: "GDPR-DPIA", label: "GDPR - Data Protection Impact Assessment" },
                            { value: "CCPA-PIA", label: "CCPA Privacy Impact Assessment" },
                          ]}
                        />
                      </Form.Item>
                    </Flex>

                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Nature of processing</Text>
                          <Flex gap="small" align="center">
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 8 }}>
                              AI
                            </Tag>
                            <Text type="success" style={{ fontSize: 12 }}>
                              HIGH CONFIDENCE
                            </Text>
                          </Flex>
                        </Flex>
                      }
                      name="nature"
                    >
                      <Input.TextArea
                        rows={6}
                        defaultValue="The system uses machine learning algorithms to analyze customer purchase history and browsing behavior to generate personalized product recommendations. Data is ingested via API from the core commerce engine and processed in a secure isolated environment."
                        placeholder="How will you process the data? Describe the data flow, assets, and technology used."
                      />
                    </Form.Item>

                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Scope (data categories)</Text>
                          <Tag color={CUSTOM_TAG_COLOR.CORINTH} style={{ marginLeft: 8 }}>
                            JG + AI
                          </Tag>
                        </Flex>
                      }
                      name="scope"
                    >
                      <div>
                        <Flex gap="small" wrap="wrap" style={{ marginBottom: 12 }}>
                          <Tag
                            color={CUSTOM_TAG_COLOR.MARBLE}
                            closable
                            onClose={() => {}}
                          >
                            Personal Identifiable Information (PII)
                          </Tag>
                          <Tag
                            color={CUSTOM_TAG_COLOR.MARBLE}
                            closable
                            onClose={() => {}}
                          >
                            Behavioral Data
                          </Tag>
                          <Button type="dashed" size="small" icon={<PlusOutlined />}>
                            Add Category
                          </Button>
                        </Flex>
                        <Input.TextArea
                          rows={3}
                          defaultValue="Names, email addresses, IP addresses, purchase history, and clickstream data."
                          placeholder="What personal data will be processed? Does it include special categories?"
                        />
                      </div>
                    </Form.Item>

                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Context of processing</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="context"
                    >
                      <Input.TextArea
                        rows={4}
                        defaultValue="Data subjects are existing customers who have opted-in to marketing communications. The relationship is direct B2C. There are no known vulnerable groups in the standard customer base."
                        placeholder="What is the nature of your relationship with the individuals? Are they vulnerable?"
                      />
                    </Form.Item>
                  </Space>
                </Form>
              </Space>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("2") ? (
                    <Text strong style={{ fontSize: 16 }}>Necessity</Text>
                  ) : (
                    <Flex gap="large" align="center" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ minWidth: 60, flexShrink: 0 }}>
                        <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
                          Step
                        </Text>
                        <Text strong style={{ fontSize: 20, display: "block", lineHeight: 1 }}>
                          2
                        </Text>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 8, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            Necessity
                          </Text>
                        </Flex>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Updated 5m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 4 }}>AI</Tag>
                          </Text>
                        </div>
                        <Flex gap="large" wrap="wrap">
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            <Text strong>Fields:</Text> 4/4
                          </Text>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: palette.FIDESUI_SUCCESS,
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>Risk Level:</Text> Low
                            </Text>
                          </Flex>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: palette.FIDESUI_SUCCESS,
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>AI Confidence:</Text> High
                            </Text>
                          </Flex>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                  </div>
                </>
              }
              key="2"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <Form.Item
                    label={
                      <Flex justify="space-between" align="center">
                        <Text strong>Purpose of processing</Text>
                        <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 8 }}>
                          AI
                        </Tag>
                      </Flex>
                    }
                    name="purpose"
                  >
                    <Input.TextArea rows={4} />
                  </Form.Item>
                </Space>
              </Form>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("3") ? (
                    <Text strong style={{ fontSize: 16 }}>Assessment of risks</Text>
                  ) : (
                    <Flex gap="large" align="center" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ minWidth: 60, flexShrink: 0 }}>
                        <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
                          Step
                        </Text>
                        <Text strong style={{ fontSize: 20, display: "block", lineHeight: 1 }}>
                          3
                        </Text>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 8, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            Assessment of risks
                          </Text>
                        </Flex>
                        <div style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Updated 15m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                            {" + "}
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 4 }}>AI</Tag>
                          </Text>
                        </div>
                        <Flex gap="large" wrap="wrap">
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            <Text strong>Fields:</Text> 2/4
                          </Text>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: "#faad14",
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>Risk Level:</Text> Medium
                            </Text>
                          </Flex>
                          <Flex align="center" gap="small">
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                backgroundColor: palette.FIDESUI_WARNING,
                              }}
                            />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              <Text strong>AI Confidence:</Text> Medium
                            </Text>
                          </Flex>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.WARNING}>In progress</Tag>
                  </div>
                </>
              }
              key="3"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <Form.Item
                    label={
                      <Flex justify="space-between" align="center">
                        <Text strong>Identified risks</Text>
                        <Flex gap="small">
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 4 }}>AI</Tag>
                        </Flex>
                      </Flex>
                    }
                    name="risks"
                  >
                    <Input.TextArea rows={4} />
                  </Form.Item>
                </Space>
              </Form>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("4") ? (
                    <Text strong style={{ fontSize: 16 }}>Measures to address risks</Text>
                  ) : (
                    <Flex gap="large" align="center" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ minWidth: 60, flexShrink: 0 }}>
                        <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
                          Step
                        </Text>
                        <Text strong style={{ fontSize: 20, display: "block", lineHeight: 1 }}>
                          4
                        </Text>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 8, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            Measures to address risks
                          </Text>
                        </Flex>
                        <Flex gap="middle" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Pending Step 3 completion
                          </Text>
                        </Flex>
                        <Flex gap="large" wrap="wrap">
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            <Text strong>Fields:</Text> 0/3
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Incomplete</Tag>
                  </div>
                </>
              }
              key="4"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <Form.Item
                    label={
                      <Flex justify="space-between" align="center">
                        <Text strong>Measures to address risks</Text>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                      </Flex>
                    }
                    name="measures"
                  >
                    <Input.TextArea rows={4} />
                  </Form.Item>
                </Space>
              </Form>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("5") ? (
                    <Text strong style={{ fontSize: 16 }}>Sign off & Review</Text>
                  ) : (
                    <Flex gap="large" align="center" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ minWidth: 60, flexShrink: 0 }}>
                        <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
                          Step
                        </Text>
                        <Text strong style={{ fontSize: 20, display: "block", lineHeight: 1 }}>
                          5
                        </Text>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 8, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            Sign off & Review
                          </Text>
                        </Flex>
                        <Flex gap="middle" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Final approval required
                          </Text>
                        </Flex>
                        <Flex gap="large" wrap="wrap">
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            <Text strong>Fields:</Text> 0/2
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Incomplete</Tag>
                  </div>
                </>
              }
              key="5"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <Form.Item
                    label={
                      <Flex justify="space-between" align="center">
                        <Text strong>Final review</Text>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                      </Flex>
                    }
                    name="review"
                  >
                    <Input.TextArea rows={4} />
                  </Form.Item>
                </Space>
              </Form>
            </Panel>
          </Collapse>
        </Space>
      </div>

      <Drawer
        title="AI Context - Slack Conversation"
        placement="right"
        onClose={() => setIsDrawerOpen(false)}
        open={isDrawerOpen}
        width={480}
        styles={{
          body: {
            padding: 0,
            display: "flex",
            flexDirection: "column",
            height: "100%",
          },
        }}
      >
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            backgroundColor: "#fafafa",
          }}
        >
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: "flex",
                gap: 12,
                justifyContent: msg.sender === "astralis" ? "flex-start" : "flex-end",
                flexDirection: msg.sender === "astralis" ? "row" : "row-reverse",
              }}
            >
              <Avatar
                style={{
                  backgroundColor: msg.sender === "astralis" ? palette.FIDESUI_MINOS : palette.FIDESUI_MARBLE,
                  flexShrink: 0,
                }}
                size={32}
              >
                {msg.sender === "astralis" ? "A" : "JG"}
              </Avatar>
              <div
                style={{
                  maxWidth: "75%",
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    justifyContent: msg.sender === "astralis" ? "flex-start" : "flex-end",
                  }}
                >
                  <Text strong style={{ fontSize: 13 }}>
                    {msg.senderName}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {msg.timestamp}
                  </Text>
                </div>
                <div
                  style={{
                    padding: "12px 16px",
                    borderRadius: 12,
                    backgroundColor: msg.sender === "astralis" ? "white" : palette.FIDESUI_MINOS,
                    color: msg.sender === "astralis" ? "#1a1a1a" : "white",
                    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                    wordWrap: "break-word",
                  }}
                >
                  <Text
                    style={{
                      fontSize: 14,
                      lineHeight: "20px",
                      color: msg.sender === "astralis" ? "#1a1a1a" : "white",
                      margin: 0,
                    }}
                  >
                    {msg.message}
                  </Text>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Drawer>
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
