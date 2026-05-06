import { ChakraHStack as HStack, CUSTOM_TAG_COLOR, Tag } from "fidesui";

import {
  BLOCKING_BADGES,
  HEALTH_BADGE_LABELS,
  HealthBadge,
  WARNING_BADGES,
} from "./mock-data";

const tagColorFor = (badge: HealthBadge): CUSTOM_TAG_COLOR => {
  if (badge === "healthy") {
    return CUSTOM_TAG_COLOR.SUCCESS;
  }
  if (badge === "manual") {
    return CUSTOM_TAG_COLOR.DEFAULT;
  }
  if (BLOCKING_BADGES.has(badge)) {
    return CUSTOM_TAG_COLOR.ERROR;
  }
  if (WARNING_BADGES.has(badge)) {
    return CUSTOM_TAG_COLOR.CAUTION;
  }
  return CUSTOM_TAG_COLOR.DEFAULT;
};

interface HealthBadgesProps {
  badges: HealthBadge[];
}

export const HealthBadges = ({ badges }: HealthBadgesProps) => (
  <HStack spacing={1} flexWrap="wrap" data-testid="health-badges">
    {badges.map((b) => (
      <Tag key={b} color={tagColorFor(b)}>
        {HEALTH_BADGE_LABELS[b]}
      </Tag>
    ))}
  </HStack>
);
