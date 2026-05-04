import { Flex, Tag, Tooltip } from "fidesui";
import { useEffect, useRef, useState } from "react";

import type { DetailsDrawerProps } from "./types";

export const DetailsDrawerTitle = ({
  title,
  titleIcon,
  titleTag,
}: Pick<DetailsDrawerProps, "title" | "titleIcon" | "titleTag">) => {
  const titleRef = useRef<HTMLSpanElement>(null);
  const [isTruncated, setIsTruncated] = useState(false);

  useEffect(() => {
    const el = titleRef.current;
    if (!el) {
      return undefined;
    }
    const update = () => setIsTruncated(el.scrollWidth > el.clientWidth);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, [title]);

  return (
    <Flex align="center" gap="small">
      {titleIcon}
      <Tooltip title={isTruncated ? title : null}>
        <span ref={titleRef} className="grow truncate">
          {title}
        </span>
      </Tooltip>
      {titleTag && <Tag {...titleTag} />}
    </Flex>
  );
};

export default DetailsDrawerTitle;
