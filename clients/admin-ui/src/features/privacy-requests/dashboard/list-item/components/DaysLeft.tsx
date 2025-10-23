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
    let color = CUSTOM_TAG_COLOR.ERROR;
    if (percentage < 25) {
      color = CUSTOM_TAG_COLOR.ERROR;
    } else if (percentage >= 75) {
      color = CUSTOM_TAG_COLOR.SUCCESS;
    } else {
      color = CUSTOM_TAG_COLOR.WARNING;
    }
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
