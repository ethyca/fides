/**
 * Mock dashboard statistics for the action center prototype.
 *
 * Each entry must be internally consistent:
 *   status_counts values must sum to approval_progress.total
 *   needReview (classified + detected) = total - approved
 */

import { AggregateStatisticsResponse } from "~/types/api/models/AggregateStatisticsResponse";

type MockEntry = Partial<AggregateStatisticsResponse>;
type MockByStewartKey = Record<string, MockEntry>;

const MOCK_DASHBOARD_STATS: Record<string, MockByStewartKey> = {
  // ─── Data stores (hundreds of thousands) ───────────────────────
  datastore: {
    __default: {
      // 297K total: 185K approved, 112K need review
      approval_progress: { approved: 185000, total: 297000, percentage: 62 },
      total_monitors: 28,
      last_updated: new Date(Date.now() - 12 * 60000).toISOString(), // 12 min ago
      status_counts: {
        addition: 45000, // detected/unclassified
        classifying: 12000,
        classified: 31000,
        reviewed: 24000,
        monitored: 185000, // approved
      },
      top_classifications: {
        data_categories: [
          { name: "user.contact.email", count: 65340, percentage: 22 },
          { name: "user.financial.bank_account", count: 53460, percentage: 18 },
          { name: "user.government_id", count: 41580, percentage: 14 },
          { name: "user.name", count: 35640, percentage: 12 },
          { name: "user.contact.phone_number", count: 26730, percentage: 9 },
        ],
        data_uses: [],
      },
    },
    // Alice: 18 monitors, 210K total, 120K approved (57%)
    alice: {
      approval_progress: { approved: 120000, total: 210000, percentage: 57 },
      total_monitors: 18,
      last_updated: new Date(Date.now() - 8 * 60000).toISOString(),
      status_counts: {
        addition: 32000,
        classifying: 9000,
        classified: 28000,
        reviewed: 21000,
        monitored: 120000,
      },
      top_classifications: {
        data_categories: [
          { name: "user.contact.email", count: 52500, percentage: 25 },
          { name: "user.financial.bank_account", count: 39900, percentage: 19 },
          { name: "user.government_id", count: 23100, percentage: 11 },
          { name: "user.name", count: 21000, percentage: 10 },
        ],
        data_uses: [],
      },
    },
    // Bob: 10 monitors, 87K total, 65K approved (75%)
    bob: {
      approval_progress: { approved: 65000, total: 87000, percentage: 75 },
      total_monitors: 10,
      last_updated: new Date(Date.now() - 25 * 60000).toISOString(),
      status_counts: {
        addition: 8000,
        classifying: 2000,
        classified: 5000,
        reviewed: 7000,
        monitored: 65000,
      },
      top_classifications: {
        data_categories: [
          { name: "user.contact.email", count: 17400, percentage: 20 },
          { name: "user.financial.bank_account", count: 13920, percentage: 16 },
          { name: "user.contact.phone_number", count: 12180, percentage: 14 },
        ],
        data_uses: [],
      },
    },
  },

  // ─── Infrastructure (hundreds) ─────────────────────────────────
  infrastructure: {
    __default: {
      // 342 total: 186 approved, 156 need review
      approval_progress: { approved: 186, total: 342, percentage: 54 },
      total_monitors: 4,
      last_updated: new Date(Date.now() - 45 * 60000).toISOString(),
      status_counts: {
        addition: 89, // detected
        classified: 67,
        monitored: 186, // approved
      },
      vendor_counts: { known: 210, unknown: 132 },
      top_classifications: {
        data_categories: [],
        data_uses: [
          { name: "analytics", count: 106, percentage: 31 },
          { name: "essential.service.operations", count: 82, percentage: 24 },
          { name: "marketing.advertising", count: 62, percentage: 18 },
        ],
      },
    },
    // Alice: no infra monitors
    alice: {
      approval_progress: { approved: 0, total: 0, percentage: 0 },
      total_monitors: 0,
      status_counts: {},
      vendor_counts: { known: 0, unknown: 0 },
    },
    // Bob: owns all infra (same as default)
    bob: {
      approval_progress: { approved: 186, total: 342, percentage: 54 },
      total_monitors: 4,
      last_updated: new Date(Date.now() - 45 * 60000).toISOString(),
      status_counts: {
        addition: 89,
        classified: 67,
        monitored: 186,
      },
      vendor_counts: { known: 210, unknown: 132 },
      top_classifications: {
        data_categories: [],
        data_uses: [
          { name: "analytics", count: 106, percentage: 31 },
          { name: "essential.service.operations", count: 82, percentage: 24 },
          { name: "marketing.advertising", count: 62, percentage: 18 },
        ],
      },
    },
  },

  // ─── Websites (tens of thousands) ──────────────────────────────
  website: {
    __default: {
      // 18.4K total: 6.2K approved, 12.2K need review
      approval_progress: { approved: 6200, total: 18400, percentage: 34 },
      total_monitors: 12,
      last_updated: new Date(Date.now() - 3 * 60000).toISOString(),
      status_counts: {
        addition: 8200, // detected/uncategorized
        classified: 4000, // categorized
        monitored: 6200, // approved
      },
      top_classifications: {
        data_categories: [],
        data_uses: [
          { name: "marketing.advertising.first_party.targeted", count: 6992, percentage: 38 },
          { name: "analytics", count: 5336, percentage: 29 },
          { name: "essential", count: 4048, percentage: 22 },
        ],
      },
    },
    // Alice: 8 monitors, 14.8K total, 4.1K approved (28%)
    alice: {
      approval_progress: { approved: 4100, total: 14800, percentage: 28 },
      total_monitors: 8,
      last_updated: new Date(Date.now() - 5 * 60000).toISOString(),
      status_counts: {
        addition: 7200,
        classified: 3500,
        monitored: 4100,
      },
      top_classifications: {
        data_categories: [],
        data_uses: [
          { name: "marketing.advertising.first_party.targeted", count: 6216, percentage: 42 },
          { name: "analytics", count: 4588, percentage: 31 },
          { name: "essential", count: 2664, percentage: 18 },
        ],
      },
    },
    // Bob: no website monitors
    bob: {
      approval_progress: { approved: 0, total: 0, percentage: 0 },
      total_monitors: 0,
      status_counts: {},
    },
  },
};

/**
 * Get mock stats for a monitor type, scoped to a steward filter.
 * Always returns consistent data — handles null, undefined, and empty string.
 */
export const getDashboardMockStats = (
  monitorType: string,
  stewardKey: string | null | undefined,
  stewardName: string | undefined,
): MockEntry | undefined => {
  const typeData = MOCK_DASHBOARD_STATS[monitorType];
  if (!typeData) return undefined;

  // No filter active → return defaults
  if (!stewardKey) return typeData.__default;

  // Match by steward name (prototype hack)
  if (stewardName?.toLowerCase().includes("alice")) return typeData.alice;
  if (stewardName?.toLowerCase().includes("bob")) return typeData.bob;

  // Unknown steward → default
  return typeData.__default;
};
