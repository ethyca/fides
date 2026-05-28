/**
 * MOCKUP ONLY — for design review, not production use.
 *
 * Consent Analytics Widget mockup for the Consent Report page.
 * Follows the Action Center ProgressCard visual pattern with
 * filter dropdowns similar to MonitorListSearchForm.
 *
 * Ticket: ENG-3623
 */

import {
  Badge,
  Card,
  Col,
  Descriptions,
  Divider,
  Flex,
  Form,
  Row,
  Select,
  StackedBarChart,
  Statistic,
  Text,
  Title,
  Tooltip,
} from "fidesui";

// ---------------------------------------------------------------------------
// Mock data – replace with RTK Query hooks against
// /dashboard/consent-analytics when API is ready
// ---------------------------------------------------------------------------

const MOCK_NOTICES = [
  { label: "All notices", value: "all" },
  { label: "Performance", value: "performance" },
  { label: "Targeting / Advertising", value: "targeting" },
  { label: "Functional", value: "functional" },
  { label: "Analytics", value: "analytics" },
];

const MOCK_REGIONS = [
  { label: "All regions", value: "all" },
  { label: "US - California", value: "us_ca" },
  { label: "US - Virginia", value: "us_va" },
  { label: "EU - France", value: "eu_fr" },
  { label: "EU - Germany", value: "eu_de" },
  { label: "UK", value: "gb" },
];

const MOCK_DOMAINS = [
  { label: "All domains", value: "all" },
  { label: "www.example.com", value: "www.example.com" },
  { label: "app.example.com", value: "app.example.com" },
  { label: "shop.example.com", value: "shop.example.com" },
];

const MOCK_TIME_PERIODS = [
  { label: "Past 24 hours", value: "24h" },
  { label: "Past 7 days", value: "7d" },
  { label: "Past 30 days", value: "30d" },
  { label: "Past 90 days", value: "90d" },
];

// ---------------------------------------------------------------------------
// Consent Rate Card — mirrors ProgressCard layout
// ---------------------------------------------------------------------------

interface ConsentRateCardProps {
  title: string;
  ratePercent: number;
  uniqueUsers: number;
  totalUsers: number;
  barData: { optIn: number; optOut: number; noAction: number };
  breakdownLabel: string;
  breakdown: { label: string; value: number }[];
}

const ConsentRateCard = ({
  title,
  ratePercent,
  uniqueUsers,
  totalUsers,
  barData,
  breakdownLabel,
  breakdown,
}: ConsentRateCardProps) => {
  const barTotal = barData.optIn + barData.optOut + barData.noAction;

  return (
    <Flex className="w-full" vertical>
      <Title level={5} className="whitespace-nowrap">
        {title}
      </Title>

      {/* Large stat */}
      <Tooltip
        color="white"
        rootClassName="max-w-[400px]"
        title={
          <div>
            <Text type="secondary" strong className="text-xs">
              Unique devices
            </Text>
            <Descriptions size="small" column={1} layout="horizontal">
              <Descriptions.Item label="Opted in">
                {barData.optIn.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Opted out">
                {barData.optOut.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="No action">
                {barData.noAction.toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </div>
        }
      >
        <Statistic
          value={ratePercent}
          suffix="%"
          valueStyle={{ fontWeight: 600 }}
        />
      </Tooltip>

      <Text>
        {uniqueUsers.toLocaleString()} of {totalUsers.toLocaleString()} unique
        devices
      </Text>

      {/* Stacked bar */}
      <div className="mt-2">
        <StackedBarChart
          data={{
            progress: {
              approved: barData.optIn,
              classified: barData.optOut,
              unlabeled: barData.noAction,
              empty: barTotal === 0 ? 1 : 0,
            },
          }}
          segments={[
            { key: "approved", color: "colorSuccess", label: "Opt-in" },
            { key: "classified", color: "colorError", label: "Opt-out" },
            { key: "unlabeled", color: "colorPrimaryBg", label: "No action" },
            { key: "empty", color: "colorPrimaryBg", label: "" },
          ]}
          hideTooltip
        />
        <Tooltip
          color="white"
          rootClassName="max-w-[400px]"
          title={
            breakdown.length > 0 ? (
              <div>
                <Text type="secondary" strong className="text-xs">
                  {breakdownLabel}
                </Text>
                <Descriptions size="small" column={1} layout="horizontal">
                  {breakdown.map(({ label, value }) => (
                    <Descriptions.Item label={label} key={label}>
                      {value}%
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </div>
            ) : undefined
          }
        >
          <Flex gap="small" rootClassName="w-max overflow-hidden">
            <Badge
              status="success"
              text={`${barData.optIn.toLocaleString()} opt-in`}
            />
            <Badge
              status="error"
              text={`${barData.optOut.toLocaleString()} opt-out`}
            />
            <Badge
              status="default"
              text={`${barData.noAction.toLocaleString()} no action`}
            />
          </Flex>
        </Tooltip>
      </div>
    </Flex>
  );
};

// ---------------------------------------------------------------------------
// Main Widget
// ---------------------------------------------------------------------------

const ConsentAnalyticsWidgetMockup = () => {
  return (
    <Card className="mb-4" data-testid="consent-analytics-widget">
      {/* Filter bar — mirrors MonitorListSearchForm */}
      <Form layout="inline" className="mb-4 flex grow gap-2">
        <Form.Item label="Notice">
          <Select
            options={MOCK_NOTICES}
            defaultValue="all"
            className="min-w-[200px]"
            placeholder="Notice"
            allowClear
            data-testid="notice-filter"
            aria-label="Filter by notice"
          />
        </Form.Item>
        <Form.Item label="Region">
          <Select
            options={MOCK_REGIONS}
            defaultValue="all"
            className="min-w-[180px]"
            placeholder="Region"
            allowClear
            showSearch={{ optionFilterProp: "label" }}
            data-testid="region-filter"
            aria-label="Filter by region"
          />
        </Form.Item>
        <Form.Item label="Domain">
          <Select
            options={MOCK_DOMAINS}
            defaultValue="all"
            className="min-w-[200px]"
            placeholder="Domain"
            allowClear
            showSearch={{ optionFilterProp: "label" }}
            data-testid="domain-filter"
            aria-label="Filter by domain"
          />
        </Form.Item>
        <Form.Item label="Period">
          <Select
            options={MOCK_TIME_PERIODS}
            defaultValue="30d"
            className="min-w-[160px]"
            data-testid="period-filter"
            aria-label="Filter by time period"
          />
        </Form.Item>
      </Form>

      {/* Stats cards row — mirrors MonitorStats horizontal layout */}
      <Flex className="w-full" gap="middle">
        {/* Card 1: Overall Opt-in Rate */}
        <ConsentRateCard
          title="Opt-in rate"
          ratePercent={62.4}
          uniqueUsers={18720}
          totalUsers={30000}
          barData={{ optIn: 18720, optOut: 8280, noAction: 3000 }}
          breakdownLabel="By notice"
          breakdown={[
            { label: "Functional", value: 78.2 },
            { label: "Analytics", value: 65.1 },
            { label: "Performance", value: 58.7 },
            { label: "Targeting", value: 41.3 },
          ]}
        />

        <Divider type="vertical" className="h-auto self-stretch" />

        {/* Card 2: Opt-out Rate */}
        <ConsentRateCard
          title="Opt-out rate"
          ratePercent={27.6}
          uniqueUsers={8280}
          totalUsers={30000}
          barData={{ optIn: 18720, optOut: 8280, noAction: 3000 }}
          breakdownLabel="By notice"
          breakdown={[
            { label: "Targeting", value: 58.7 },
            { label: "Performance", value: 41.3 },
            { label: "Analytics", value: 34.9 },
            { label: "Functional", value: 21.8 },
          ]}
        />

        <Divider type="vertical" className="h-auto self-stretch" />

        {/* Card 3: Overall Consent Rate */}
        <ConsentRateCard
          title="Consent rate"
          ratePercent={84.3}
          uniqueUsers={25310}
          totalUsers={30030}
          barData={{ optIn: 18720, optOut: 6590, noAction: 4720 }}
          breakdownLabel="Interaction method"
          breakdown={[
            { label: "Accept", value: 62.4 },
            { label: "Reject", value: 18.2 },
            { label: "Save (custom)", value: 3.7 },
            { label: "Dismiss", value: 15.7 },
          ]}
        />

        <Divider type="vertical" className="h-auto self-stretch" />

        {/* Card 4: Notices Served */}
        <Flex className="w-full" vertical>
          <Title level={5} className="whitespace-nowrap">
            Notices served
          </Title>
          <Statistic
            value={30030}
            valueStyle={{ fontWeight: 600 }}
          />
          <Text>total notices served to unique devices</Text>
          <div className="mt-2">
            <Descriptions size="small" column={1} layout="horizontal">
              <Descriptions.Item label="Banner">
                22,140
              </Descriptions.Item>
              <Descriptions.Item label="Modal">
                5,410
              </Descriptions.Item>
              <Descriptions.Item label="Privacy center">
                2,480
              </Descriptions.Item>
            </Descriptions>
          </div>
        </Flex>
      </Flex>

      {/* TCF section — conditionally shown when TCF notices exist */}
      <Divider className="my-4" />
      <Flex className="w-full" gap="middle">
        <Flex className="w-full" vertical>
          <Title level={5}>TCF consent</Title>
          <Row gutter={24}>
            <Col span={8}>
              <Statistic
                title="Reject-all rate"
                value={14.8}
                suffix="%"
                valueStyle={{ color: "#cf1322", fontWeight: 600 }}
              />
              <Text type="secondary" className="text-xs">
                856 of 5,784 TCF interactions
              </Text>
            </Col>
            <Col span={8}>
              <Statistic
                title="Accept-all rate"
                value={68.2}
                suffix="%"
                valueStyle={{ color: "#3f8600", fontWeight: 600 }}
              />
              <Text type="secondary" className="text-xs">
                3,946 of 5,784 TCF interactions
              </Text>
            </Col>
            <Col span={8}>
              <Statistic
                title="Custom preferences"
                value={17.0}
                suffix="%"
                valueStyle={{ fontWeight: 600 }}
              />
              <Text type="secondary" className="text-xs">
                982 of 5,784 TCF interactions
              </Text>
            </Col>
          </Row>
        </Flex>
      </Flex>
    </Card>
  );
};

export default ConsentAnalyticsWidgetMockup;
