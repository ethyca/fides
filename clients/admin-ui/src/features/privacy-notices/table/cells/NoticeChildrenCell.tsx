import { ListExpandableCell } from "~/features/common/table/cells";
import { LimitedPrivacyNoticeResponseSchema } from "~/types/api";

export const getNoticeChildrenNames = (
  children: LimitedPrivacyNoticeResponseSchema[] | undefined | null,
): string[] => {
  if (!children) {
    return [];
  }
  const values: string[] = [];
  children.forEach((child) => {
    const value = child.name;
    if (value !== undefined) {
      values.push(value);
    }
  });
  return values;
};

const NoticeChildrenCell = ({
  value,
}: {
  value?: LimitedPrivacyNoticeResponseSchema[];
}) => {
  const childrenNames = getNoticeChildrenNames(value);

  if (childrenNames.length === 0) {
    return <span>Unassigned</span>;
  }

  return <ListExpandableCell values={childrenNames} valueSuffix="children" />;
};

export default NoticeChildrenCell;
