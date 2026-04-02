import { Flex, Text } from "fidesui";
import { motion } from "motion/react";

import { useCountUp } from "~/home/useCountUp";

import { ProgressCard, ProgressCardProps } from "./ProgressCard";
import { MONITOR_TYPE_TO_LABEL } from "./utils";

const ANIMATION_DURATION = 800;

interface AnimatedProgressCardProps extends ProgressCardProps {
  /** The monitor_type key, used for the empty state message */
  monitorType?: string;
  /** Whether this card has any monitors (controls empty state) */
  hasMonitors: boolean;
}

const AnimatedProgressCard = ({
  monitorType,
  hasMonitors,
  progress,
  ...rest
}: AnimatedProgressCardProps) => {
  const animatedPercent = useCountUp(
    progress.percent ?? 0,
    ANIMATION_DURATION,
  );
  const animatedNumerator = useCountUp(
    progress.numerator ?? 0,
    ANIMATION_DURATION,
  );
  const animatedDenominator = useCountUp(
    progress.denominator ?? 0,
    ANIMATION_DURATION,
  );

  const typeLabel = monitorType
    ? MONITOR_TYPE_TO_LABEL[monitorType as keyof typeof MONITOR_TYPE_TO_LABEL]
    : undefined;

  return (
    <motion.div
      animate={{ opacity: hasMonitors ? 1 : 0.5 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="relative"
    >
      <ProgressCard
        {...rest}
        progress={{
          ...progress,
          percent: animatedPercent,
          numerator: animatedNumerator,
          denominator: animatedDenominator,
        }}
      />
      {!hasMonitors && typeLabel && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.2 }}
        >
          <Flex
            justify="center"
            className="absolute inset-0 items-end pb-4"
          >
            <Text type="secondary" className="text-xs">
              No {typeLabel.toLowerCase()} monitors
            </Text>
          </Flex>
        </motion.div>
      )}
    </motion.div>
  );
};

export default AnimatedProgressCard;
