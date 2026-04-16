import dayjs from "dayjs";
import { CUSTOM_TAG_COLOR, Tag, Tooltip } from "fidesui";

import { PrivacyRequestStatus } from "~/types/api";

import { formatDate } from "../../../../common/utils";

const DAY_IRRELEVANT_STATUSES = [
  PrivacyRequestStatus.COMPLETE,
  PrivacyRequestStatus.CANCELED,
  PrivacyRequestStatus.DENIED,
  PrivacyRequestStatus.IDENTITY_UNVERIFIED,
];

export const DaysLeft = ({
  status,
  daysLeft,
  timeframe = 45,
}: {
  status: PrivacyRequestStatus;
  daysLeft: number | undefined | null;
  timeframe: number | undefined | null;
}) => {
  const showBadge =
    daysLeft !== undefined &&
    daysLeft !== null &&
    timeframe !== undefined &&
    timeframe !== null &&
    !DAY_IRRELEVANT_STATUSES.includes(status);

  if (showBadge) {
    const isOverdue = daysLeft < 0;
    const percentage = (100 * daysLeft) / timeframe;
    const color =
      isOverdue || percentage < 25
        ? CUSTOM_TAG_COLOR.ERROR
        : CUSTOM_TAG_COLOR.DEFAULT;
    const label = isOverdue
      ? `${Math.abs(daysLeft)} days overdue`
      : `${daysLeft} days left`;
    return (
      <div>
        <Tag color={color} variant="filled">
          <Tooltip title={formatDate(dayjs().add(daysLeft, "day").toDate())}>
            {label}
          </Tooltip>
        </Tag>
      </div>
    );
  }

  return null;
};
