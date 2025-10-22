import { AntFlex as Flex, AntTag as Tag } from "fidesui";

import type { DetailsDrawerProps } from "./types";

export const DetailsDrawerTitle = ({
  title,
  titleIcon,
  titleTag,
}: Pick<DetailsDrawerProps, "title" | "titleIcon" | "titleTag">) => {
  return (
    <Flex align="center" gap="small">
      {titleIcon}
      <span>{title}</span>
      {titleTag && <Tag {...titleTag} />}
    </Flex>
  );
};

export default DetailsDrawerTitle;
