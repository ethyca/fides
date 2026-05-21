// PROTOTYPE — delete with TCF history
import { CUSTOM_TAG_COLOR } from "fidesui";

export type HistoryEventType =
  | "config_update"
  | "restriction_added"
  | "restriction_updated"
  | "compass_sync";

export type HistorySource = { kind: "fides" } | { kind: "user"; name: string };

export interface HistoryEvent {
  id: string;
  type: HistoryEventType;
  timestamp: string;
  previousHash: string | null;
  newHash: string;
  source: HistorySource;
}

export const EVENT_TYPE_LABEL: Record<HistoryEventType, string> = {
  config_update: "Config update",
  restriction_added: "Restriction added",
  restriction_updated: "Restriction updated",
  compass_sync: "Compass sync",
};

export const EVENT_TYPE_COLOR: Record<HistoryEventType, CUSTOM_TAG_COLOR> = {
  config_update: CUSTOM_TAG_COLOR.MARBLE,
  restriction_added: CUSTOM_TAG_COLOR.NECTAR,
  restriction_updated: CUSTOM_TAG_COLOR.OLIVE,
  compass_sync: CUSTOM_TAG_COLOR.SANDSTONE,
};

export const MOCK_TCF_EXPERIENCE_ID = "tcf-mock-experience";
export const MOCK_TCF_EXPERIENCE_NAME = "TCF";

export const MOCK_TCF_HISTORY: HistoryEvent[] = [
  {
    id: "evt-10",
    type: "restriction_updated",
    timestamp: "2026-05-21T14:22:08+01:00",
    previousHash: "i1f9g0h2",
    newHash: "j2g0h1i3",
    source: { kind: "user", name: "Sarah Chen" },
  },
  {
    id: "evt-9",
    type: "restriction_added",
    timestamp: "2026-05-21T11:05:42+01:00",
    previousHash: "h0e8f9g1",
    newHash: "i1f9g0h2",
    source: { kind: "user", name: "Jack Gale" },
  },
  {
    id: "evt-8",
    type: "compass_sync",
    timestamp: "2026-05-21T08:30:00+01:00",
    previousHash: "g9d7e8f0",
    newHash: "h0e8f9g1",
    source: { kind: "fides" },
  },
  {
    id: "evt-7",
    type: "config_update",
    timestamp: "2026-05-20T22:45:19+01:00",
    previousHash: "f8c6d7e9",
    newHash: "g9d7e8f0",
    source: { kind: "user", name: "Alex Morrison" },
  },
  {
    id: "evt-6",
    type: "restriction_added",
    timestamp: "2026-05-20T18:11:53+01:00",
    previousHash: "e7b5c6d8",
    newHash: "f8c6d7e9",
    source: { kind: "user", name: "Sarah Chen" },
  },
  {
    id: "evt-5",
    type: "config_update",
    timestamp: "2026-05-20T16:07:15+01:00",
    previousHash: "d6a4b5c7",
    newHash: "e7b5c6d8",
    source: { kind: "user", name: "Jack Gale" },
  },
  {
    id: "evt-4",
    type: "restriction_updated",
    timestamp: "2026-05-19T16:07:15+01:00",
    previousHash: "c5f3a4b6",
    newHash: "d6a4b5c7",
    source: { kind: "user", name: "Alex Morrison" },
  },
  {
    id: "evt-3",
    type: "compass_sync",
    timestamp: "2026-05-17T16:07:15+01:00",
    previousHash: "b4e2f3a5",
    newHash: "c5f3a4b6",
    source: { kind: "fides" },
  },
  {
    id: "evt-2",
    type: "restriction_added",
    timestamp: "2026-05-15T16:07:15+01:00",
    previousHash: "a3f1e2d4",
    newHash: "b4e2f3a5",
    source: { kind: "user", name: "Jack Gale" },
  },
  {
    id: "evt-1",
    type: "config_update",
    timestamp: "2026-05-13T16:07:15+01:00",
    previousHash: null,
    newHash: "a3f1e2d4",
    source: { kind: "fides" },
  },
];

export const HISTORY_TYPE_OPTIONS: Array<{
  label: string;
  value: HistoryEventType;
}> = (Object.keys(EVENT_TYPE_LABEL) as HistoryEventType[]).map((type) => ({
  label: EVENT_TYPE_LABEL[type],
  value: type,
}));

const userNames = Array.from(
  new Set(
    MOCK_TCF_HISTORY.flatMap((e) =>
      e.source.kind === "user" ? [e.source.name] : [],
    ),
  ),
);

export const HISTORY_USER_OPTIONS: Array<{ label: string; value: string }> = [
  { label: "Fides", value: "__fides__" },
  ...userNames.map((name) => ({ label: name, value: name })),
];

export const getSourceFilterValue = (source: HistorySource): string =>
  source.kind === "fides" ? "__fides__" : source.name;
