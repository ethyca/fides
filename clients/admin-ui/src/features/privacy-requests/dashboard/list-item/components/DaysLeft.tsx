import dayjs from "dayjs";
import {
  AntTag as Tag,
  AntTooltip as Tooltip,
  CUSTOM_TAG_COLOR,
} from "fidesui";

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
  daysLeft: number | undefined;
  timeframe: number | undefined;
}) => {
  const showBadge =
    !DAY_IRRELEVANT_STATUSES.includes(status) && daysLeft !== undefined;

  if (showBadge) {
    const percentage = (100 * daysLeft) / timeframe;
    const color =
      percentage < 25 ? CUSTOM_TAG_COLOR.ERROR : CUSTOM_TAG_COLOR.DEFAULT;
    return (
      <div>
        <Tag color={color} bordered={false}>
          <Tooltip title={formatDate(dayjs().add(daysLeft, "day").toDate())}>
            <>{daysLeft} days left</>
          </Tooltip>
        </Tag>
      </div>
    );
  }

  return null;
};
