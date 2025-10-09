import { formatDate, sentenceCase } from "../../common/utils";
import dayjs from "dayjs";
import {
  AntButton as Button,
  AntCol as Col,
  AntFlex as Flex,
  AntList as List,
  AntPagination as Pagination,
  AntRow as Row,
  AntSkeleton as Skeleton,
  AntSpin as Spin,
  AntTag as Tag,
  AntText as Text,
  AntTooltip as Tooltip,
  Box,
  BoxProps,
  HStack,
  Icons,
  Portal,
  useDisclosure,
  useToast,
} from "fidesui";
import { ActionType, PrivacyRequestStatus } from "~/types/api";
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
    let color = "error";
    if (percentage < 25) {
      color = "error";
    } else if (percentage >= 75) {
      color = "success";
    } else {
      color = "warning";
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
