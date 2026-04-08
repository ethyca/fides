import { Avatar, Divider, Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { GovernanceHealthData } from "../types";
import GovernanceScoreCard from "./GovernanceScoreCard";

interface GovernanceHealthDashboardProps {
  data: GovernanceHealthData;
}

// Each pillar contributes score/4 so they stack to the overall score
const TREND_DATA = [
  { month: "Oct", annotation: 5.5, compliance: 12, purpose: 8.75, ownership: 7.5 },
  { month: "Nov", annotation: 7.5, compliance: 13.75, purpose: 10.5, ownership: 9.5 },
  { month: "Dec", annotation: 9.5, compliance: 15.5, purpose: 13.75, ownership: 11.25 },
  { month: "Jan", annotation: 10.5, compliance: 17.5, purpose: 17, ownership: 13 },
  { month: "Feb", annotation: 12.5, compliance: 20.5, purpose: 19.5, ownership: 14.5 },
  { month: "Mar", annotation: 14.5, compliance: 23, purpose: 21, ownership: 16.5 },
];
// Stacked totals: 34 → 41 → 50 → 58 → 67 → 75

const PILLAR_SERIES = [
  { key: "annotation", name: "Annotation", color: palette.FIDESUI_TERRACOTTA },
  { key: "compliance", name: "Compliance", color: palette.FIDESUI_SANDSTONE },
  { key: "purpose", name: "Purpose", color: palette.FIDESUI_OLIVE },
  { key: "ownership", name: "Ownership", color: palette.FIDESUI_MINOS },
];

interface ActivityItem {
  message: string;
  time: string;
  color: string;
  steward: { initials: string };
}

const ACTIVITY: ActivityItem[] = [
  { message: "System 'Stripe' annotations completed", time: "2h ago", color: palette.FIDESUI_SUCCESS, steward: { initials: "MB" } },
  { message: "3 new issues flagged in 'Salesforce'", time: "5h ago", color: palette.FIDESUI_WARNING, steward: { initials: "LT" } },
  { message: "Data use purposes updated for marketing", time: "1d ago", color: palette.FIDESUI_SUCCESS, steward: { initials: "RS" } },
  { message: "Steward assigned to 'Segment'", time: "1d ago", color: palette.FIDESUI_INFO, steward: { initials: "RS" } },
  { message: "Monthly governance review completed", time: "3d ago", color: palette.FIDESUI_INFO, steward: { initials: "AK" } },
];

const GovernanceHealthDashboard = ({
  data,
}: GovernanceHealthDashboardProps) => (
  <div className="mb-2">
    <Flex gap={32}>
      {/* Panel 1: Donut + legend */}
      <div className="shrink-0">
        <GovernanceScoreCard data={data} />
      </div>

      {/* Panel 2: Health Over Time (stacked pillar contributions) */}
      <div className="min-w-0 flex-1 border-l border-solid border-[#f0f0f0] pl-8">
        <Flex justify="space-between" align="center" className="mb-6">
          <Text strong className="text-[10px] uppercase tracking-wider">
            Health Over Time
          </Text>
          <Flex gap={12}>
            {PILLAR_SERIES.map((s) => (
              <Flex key={s.key} align="center" gap={4}>
                <div className="size-[5px] shrink-0 rounded-full" style={{ backgroundColor: s.color }} />
                <Text className="text-[10px]" style={{ color: palette.FIDESUI_MINOS }}>{s.name}</Text>
              </Flex>
            ))}
          </Flex>
        </Flex>
        <div className="h-[170px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={TREND_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <defs>
                {PILLAR_SERIES.map((s) => (
                  <linearGradient key={s.key} id={`dash-grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={s.color} stopOpacity={0.7} />
                    <stop offset="100%" stopColor={s.color} stopOpacity={0.2} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#93969a" }} />
              <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#93969a" }} />
              <Tooltip contentStyle={{ borderRadius: 6, border: "1px solid #f0f0f0", fontSize: 11 }} />
              {PILLAR_SERIES.map((s) => (
                <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={1} fill={`url(#dash-grad-${s.key})`} stackId="health" dot={false} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Panel 3: Recent activity */}
      <div className="min-w-0 flex-1 border-l border-solid border-[#f0f0f0] pl-8">
        <Text strong className="mb-3 block text-[10px] uppercase tracking-wider">
          Recent Activity
        </Text>
        <Flex vertical gap={0}>
          {ACTIVITY.map((item, i) => (
            <Flex
              key={i}
              justify="space-between"
              align="center"
              className="border-b border-solid border-[#f5f5f5] py-1.5 last:border-b-0"
            >
              <Text className="min-w-0 flex-1 truncate text-[11px]">{item.message}</Text>
              <Flex align="center" gap={40} className="shrink-0 pl-12">
                <Avatar
                  size={20}
                  style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 9 }}
                >
                  {item.steward.initials}
                </Avatar>
                <Text type="secondary" className="text-xs">{item.time}</Text>
                <Text className="cursor-pointer text-xs" style={{ color: palette.FIDESUI_MINOS }}>
                  View &rarr;
                </Text>
              </Flex>
            </Flex>
          ))}
        </Flex>
      </div>
    </Flex>

    <Divider className="!mb-0 !mt-4" />
  </div>
);

export default GovernanceHealthDashboard;
