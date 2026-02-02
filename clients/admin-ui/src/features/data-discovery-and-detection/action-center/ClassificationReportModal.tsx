import {
  Alert,
  Card,
  Collapse,
  Descriptions,
  Flex,
  Modal,
  Progress,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "fidesui";

import {
  useGetClassificationReportQuery,
  WebsiteClassificationReport,
} from "./action-center.slice";

const { Text, Title } = Typography;

interface ClassificationReportModalProps {
  monitorId: string;
  open: boolean;
  onClose: () => void;
}

const formatPercent = (value: number): string => `${(value * 100).toFixed(1)}%`;

type TagColor = "error" | "default" | "info" | "success" | "warning" | "corinth" | "minos" | "nectar" | "olive" | "sandstone" | "terracotta" | "marble" | "alert" | "caution" | "white";

const getCategoryColor = (category: string): TagColor => {
  const colors: Record<string, TagColor> = {
    advertising: "error",
    analytics: "minos",
    social_media: "nectar",
    functional: "success",
    essential: "info",
    unknown: "default",
  };
  return colors[category.toLowerCase()] || "default";
};

const getConfidenceColor = (score: number): TagColor => {
  if (score >= 4) {
    return "success";
  }
  if (score >= 3) {
    return "warning";
  }
  return "error";
};

export const ClassificationReportModal = ({
  monitorId,
  open,
  onClose,
}: ClassificationReportModalProps) => {
  const { data: report, isLoading, error } = useGetClassificationReportQuery(
    { monitor_config_key: monitorId, sample_size: 20 },
    { skip: !open },
  );

  if (error) {
    return (
      <Modal
        title="Classification report"
        open={open}
        onCancel={onClose}
        footer={null}
        width={900}
      >
        <Alert
          type="error"
          message="Failed to load classification report"
          description="Please try again later."
        />
      </Modal>
    );
  }

  return (
    <Modal
      title="LLM classification report"
      open={open}
      onCancel={onClose}
      footer={null}
      width={1000}
      loading={isLoading}
    >
      {report && <ReportContent report={report} />}
    </Modal>
  );
};

const ReportContent = ({ report }: { report: WebsiteClassificationReport }) => {
  const { coverage, category_distribution, confidence_distribution, vendor_stats, flagged_resources, sample_classifications, by_resource_type } = report;

  return (
    <Space direction="vertical" size="large" className="w-full">
      {/* Coverage Overview */}
      <Card size="small" title="Classification coverage">
        <Flex gap="large" wrap>
          <div>
            <Text type="secondary">Total resources</Text>
            <div><Text strong style={{ fontSize: 24 }}>{coverage.total_resources}</Text></div>
          </div>
          <div>
            <Text type="secondary">Classified by Compass</Text>
            <div><Text strong style={{ fontSize: 24, color: "#52c41a" }}>{coverage.classified_by_compass}</Text></div>
          </div>
          <div>
            <Text type="secondary">Classified by LLM</Text>
            <div><Text strong style={{ fontSize: 24, color: "#1890ff" }}>{coverage.classified_by_llm}</Text></div>
          </div>
          <div>
            <Text type="secondary">Unclassified</Text>
            <div><Text strong style={{ fontSize: 24, color: coverage.unclassified > 0 ? "#faad14" : undefined }}>{coverage.unclassified}</Text></div>
          </div>
        </Flex>
        <Progress
          percent={Math.round(coverage.coverage_rate * 100)}
          status={coverage.coverage_rate === 1 ? "success" : "active"}
          format={() => `${formatPercent(coverage.coverage_rate)} coverage`}
          className="mt-4"
        />
      </Card>

      {/* Category Distribution */}
      {category_distribution.length > 0 && (
        <Card size="small" title="Category distribution">
          <Flex gap="small" wrap>
            {category_distribution.map((cat) => (
              <Tooltip key={cat.category} title={`${cat.count} resources (${formatPercent(cat.percentage)})`}>
                <Tag color={getCategoryColor(cat.category)}>
                  {cat.category}: {cat.count}
                </Tag>
              </Tooltip>
            ))}
          </Flex>
        </Card>
      )}

      {/* Confidence Distribution */}
      {confidence_distribution.length > 0 && (
        <Card size="small" title="Confidence distribution">
          <Flex gap="small" wrap>
            {confidence_distribution.map((conf) => (
              <Tag key={conf.score} color={getConfidenceColor(conf.score)}>
                Score {conf.score}: {conf.count} ({formatPercent(conf.percentage)})
              </Tag>
            ))}
          </Flex>
        </Card>
      )}

      {/* Vendor Matching Stats */}
      <Card size="small" title="Vendor matching">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Vendors identified by LLM">
            {vendor_stats.total_with_vendor_name}
          </Descriptions.Item>
          <Descriptions.Item label="Matched to Compass">
            {vendor_stats.matched_to_compass} ({formatPercent(vendor_stats.match_rate)})
          </Descriptions.Item>
          <Descriptions.Item label="Unregistered ad vendors">
            <Text type={vendor_stats.unregistered_ad_vendors > 0 ? "danger" : undefined}>
              {vendor_stats.unregistered_ad_vendors}
            </Text>
          </Descriptions.Item>
        </Descriptions>
        {vendor_stats.top_unmatched_vendors.length > 0 && (
          <div className="mt-2">
            <Text type="secondary">Top unmatched vendors: </Text>
            {vendor_stats.top_unmatched_vendors.map((name) => (
              <Tag key={name}>{name}</Tag>
            ))}
          </div>
        )}
      </Card>

      {/* Resource Type Breakdown */}
      {Object.keys(by_resource_type).length > 0 && (
        <Card size="small" title="By resource type">
          <Flex gap="small" wrap>
            {Object.entries(by_resource_type).map(([type, count]) => (
              <Tag key={type}>
                {type}: {count}
              </Tag>
            ))}
          </Flex>
        </Card>
      )}

      {/* Flagged Resources */}
      {flagged_resources.length > 0 && (
        <Collapse
          items={[
            {
              key: "flagged",
              label: (
                <Space>
                  <Text strong>Flagged resources</Text>
                  <Tag color="error">{flagged_resources.length}</Tag>
                </Space>
              ),
              children: (
                <Table
                  dataSource={flagged_resources}
                  rowKey="urn"
                  size="small"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    { title: "Domain", dataIndex: "domain", key: "domain", width: 150 },
                    { title: "Vendor", dataIndex: "vendor_name", key: "vendor_name" },
                    { title: "Category", dataIndex: "category", key: "category",
                      render: (cat: string) => <Tag color={getCategoryColor(cat)}>{cat}</Tag>
                    },
                    { title: "Flag reason", dataIndex: "flag_reason", key: "flag_reason" },
                  ]}
                />
              ),
            },
          ]}
        />
      )}

      {/* Sample Classifications */}
      {sample_classifications.length > 0 && (
        <Collapse
          items={[
            {
              key: "samples",
              label: (
                <Space>
                  <Text strong>Sample classifications</Text>
                  <Tag>{sample_classifications.length}</Tag>
                </Space>
              ),
              children: (
                <Table
                  dataSource={sample_classifications}
                  rowKey="urn"
                  size="small"
                  pagination={{ pageSize: 10 }}
                  columns={[
                    { title: "Domain", dataIndex: "domain", key: "domain", width: 120, ellipsis: true },
                    { title: "Type", dataIndex: "resource_type", key: "resource_type", width: 80 },
                    { title: "Vendor", dataIndex: "vendor_name", key: "vendor_name", width: 100, ellipsis: true },
                    { title: "Category", dataIndex: "category", key: "category", width: 100,
                      render: (cat: string) => cat ? <Tag color={getCategoryColor(cat)}>{cat}</Tag> : "-"
                    },
                    { title: "Conf.", dataIndex: "confidence", key: "confidence", width: 60,
                      render: (score: number) => score ? <Tag color={getConfidenceColor(score)}>{score}</Tag> : "-"
                    },
                    { title: "Compass", dataIndex: "compass_matched", key: "compass_matched", width: 80,
                      render: (matched: boolean) => matched ? <Tag color="success">Yes</Tag> : <Tag>No</Tag>
                    },
                    { title: "Rationale", dataIndex: "rationale", key: "rationale", ellipsis: true,
                      render: (text: string) => (
                        <Tooltip title={text}>
                          <Text ellipsis className="max-w-48">{text || "-"}</Text>
                        </Tooltip>
                      )
                    },
                  ]}
                />
              ),
            },
          ]}
        />
      )}

      {/* Placeholder for Golden Set */}
      <Alert
        type="info"
        message="Golden set comparison"
        description="Upload a golden set CSV to compare LLM classifications against ground truth and calculate accuracy metrics."
        showIcon
      />
    </Space>
  );
};

export default ClassificationReportModal;
