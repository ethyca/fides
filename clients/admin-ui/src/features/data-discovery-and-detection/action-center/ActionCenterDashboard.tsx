import { Flex, Typography } from "fidesui";
import { ConnectionType } from "~/types/api";
import { useFeatures } from "~/features/common/features";

import DataStoreSlimCard from "./DataStoreSlimCard";
import MonitorSummaryCard from "./MonitorSummaryCard";
import type { CardLayout } from "./MonitorSummaryCard";
import { MonitorAggregatedResults } from "./types";
import { MONITOR_TYPES } from "./utils/getMonitorType";

const { Text } = Typography;

// ── Full data ──
const FAKE_MONITORS: MonitorAggregatedResults[] = [
  // Web monitors
  {
    name: "Marketing Site Scanner",
    key: "marketing_site_scanner",
    connection_type: ConnectionType.WEBSITE,
    monitorType: MONITOR_TYPES.WEBSITE,
    isTestMonitor: false,
    total_updates: 84,
    updates: { cookie: 32, browser_request: 41, image: 8, iframe: 3 },
    last_monitored: "2026-03-03T14:30:00Z",
    stewards: [],
  },
  {
    name: "Customer Portal Scanner",
    key: "customer_portal_scanner",
    connection_type: ConnectionType.WEBSITE,
    monitorType: MONITOR_TYPES.WEBSITE,
    isTestMonitor: false,
    total_updates: 43,
    updates: { cookie: 18, browser_request: 15, javascript_tag: 10 },
    last_monitored: "2026-03-02T09:15:00Z",
    stewards: [],
  },
  // Datastore monitors
  {
    name: "Production BigQuery",
    key: "production_bigquery",
    connection_type: ConnectionType.BIGQUERY,
    monitorType: MONITOR_TYPES.DATASTORE,
    isTestMonitor: false,
    total_updates: 3031,
    updates: {
      unlabeled: 2400,
      in_review: 389,
      classifying: 47,
      removals: 12,
      reviewed: 183,
      classified_low_confidence: 201,
      classified_medium_confidence: 134,
      classified_high_confidence: 54,
    },
    last_monitored: "2026-03-04T08:00:00Z",
    has_failed_tasks: false,
    stewards: [],
  },
  {
    name: "Analytics Postgres",
    key: "analytics_postgres",
    connection_type: ConnectionType.POSTGRES,
    monitorType: MONITOR_TYPES.DATASTORE,
    isTestMonitor: false,
    total_updates: 628,
    updates: {
      unlabeled: 450,
      in_review: 98,
      classifying: 12,
      removals: 3,
      reviewed: 65,
      classified_low_confidence: 44,
      classified_medium_confidence: 31,
      classified_high_confidence: 23,
    },
    last_monitored: "2026-03-04T06:00:00Z",
    has_failed_tasks: false,
    stewards: [],
  },
  {
    name: "User Data MySQL",
    key: "user_data_mysql",
    connection_type: ConnectionType.MYSQL,
    monitorType: MONITOR_TYPES.DATASTORE,
    isTestMonitor: false,
    total_updates: 194,
    updates: {
      unlabeled: 150,
      in_review: 22,
      classifying: 5,
      removals: 0,
      reviewed: 17,
      classified_low_confidence: 12,
      classified_medium_confidence: 8,
      classified_high_confidence: 2,
    },
    last_monitored: "2026-03-03T22:00:00Z",
    has_failed_tasks: true,
    stewards: [],
  },
  // Infrastructure monitors
  {
    name: "Okta SSO Monitor",
    key: "okta_sso_monitor",
    connection_type: ConnectionType.OKTA,
    monitorType: MONITOR_TYPES.INFRASTRUCTURE,
    isTestMonitor: false,
    total_updates: 154,
    updates: { okta_app: 154 },
    last_monitored: "2026-03-04T10:00:00Z",
    stewards: [],
  },
];

// ── Low data (just set up, first scan with very few results) ──
const LOW_DATA_MONITORS: MonitorAggregatedResults[] = [
  {
    name: "New Site Scanner",
    key: "new_site_scanner",
    connection_type: ConnectionType.WEBSITE,
    monitorType: MONITOR_TYPES.WEBSITE,
    isTestMonitor: false,
    total_updates: 3,
    updates: { cookie: 2, browser_request: 1 },
    last_monitored: "2026-03-04T12:00:00Z",
    stewards: [],
  },
  {
    name: "Staging DB",
    key: "staging_db",
    connection_type: ConnectionType.POSTGRES,
    monitorType: MONITOR_TYPES.DATASTORE,
    isTestMonitor: false,
    total_updates: 7,
    updates: {
      unlabeled: 5,
      classifying: 2,
      in_review: 0,
      removals: 0,
      reviewed: 0,
      classified_low_confidence: 0,
      classified_medium_confidence: 0,
      classified_high_confidence: 0,
    },
    last_monitored: "2026-03-04T11:00:00Z",
    has_failed_tasks: false,
    stewards: [],
  },
  {
    name: "Okta Dev",
    key: "okta_dev",
    connection_type: ConnectionType.OKTA,
    monitorType: MONITOR_TYPES.INFRASTRUCTURE,
    isTestMonitor: false,
    total_updates: 2,
    updates: { okta_app: 2 },
    last_monitored: "2026-03-04T10:30:00Z",
    stewards: [],
  },
];

interface ActionCenterDashboardProps {
  monitors: MonitorAggregatedResults[];
}

const ActionCenterDashboard = ({
  monitors: _monitors,
}: ActionCenterDashboardProps) => {
  const {
    flags: { webMonitor: webMonitorEnabled },
  } = useFeatures();

  const cards: { type: MONITOR_TYPES; layout: CardLayout }[] = [
    { type: MONITOR_TYPES.INFRASTRUCTURE, layout: "stat-grid" },
    { type: MONITOR_TYPES.DATASTORE, layout: "sparkline" },
    ...(webMonitorEnabled
      ? [{ type: MONITOR_TYPES.WEBSITE, layout: "sparkline" as CardLayout }]
      : []),
  ];

  const monitorsByType = (
    data: MonitorAggregatedResults[],
    type: MONITOR_TYPES,
  ) => data.filter((m) => m.monitorType === type);

  const gridCols =
    cards.length === 3 ? "grid-cols-3" : `grid-cols-${cards.length}`;

  return (
    <div className="flex flex-col gap-6">
      {/* Full data */}
      <div>
        <Text
          type="secondary"
          className="text-[10px] tracking-[0.1em] mb-2 block"
          strong
        >
          FULL DATA
        </Text>
        <div className={`grid ${gridCols} gap-4`}>
          {cards.map(({ type, layout }) => (
            <MonitorSummaryCard
              key={type}
              type={type}
              monitors={monitorsByType(FAKE_MONITORS, type)}
              colorScheme="brand"
              layout={layout}
            />
          ))}
        </div>
        <Flex vertical gap={8} className="mt-3">
          <DataStoreSlimCard
            monitors={monitorsByType(FAKE_MONITORS, MONITOR_TYPES.DATASTORE)}
            variant="A"
          />
          <DataStoreSlimCard
            monitors={monitorsByType(FAKE_MONITORS, MONITOR_TYPES.DATASTORE)}
            variant="B"
          />
          <DataStoreSlimCard
            monitors={monitorsByType(FAKE_MONITORS, MONITOR_TYPES.DATASTORE)}
            variant="C"
          />
        </Flex>
      </div>

      {/* Low data */}
      <div>
        <Text
          type="secondary"
          className="text-[10px] tracking-[0.1em] mb-2 block"
          strong
        >
          NO ACTION REQUIRED
        </Text>
        <div className={`grid ${gridCols} gap-4`}>
          {cards.map(({ type, layout }) => (
            <MonitorSummaryCard
              key={`low-${type}`}
              type={type}
              monitors={monitorsByType(LOW_DATA_MONITORS, type)}
              colorScheme="brand"
              layout={layout}
            />
          ))}
        </div>
      </div>

      {/* Empty state */}
      <div>
        <Text
          type="secondary"
          className="text-[10px] tracking-[0.1em] mb-2 block"
          strong
        >
          EMPTY STATE
        </Text>
        <div className={`grid ${gridCols} gap-4`}>
          {cards.map(({ type, layout }) => (
            <MonitorSummaryCard
              key={`empty-${type}`}
              type={type}
              monitors={[]}
              colorScheme="brand"
              layout={layout}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ActionCenterDashboard;
