import { Flex, Tag, Tooltip } from "fidesui";
import { useEffect, useRef, useState } from "react";

import type { DetailsDrawerProps } from "./types";

export const DetailsDrawerTitle = ({
  title,
  titleIcon,
  titleTag,
}: Pick<DetailsDrawerProps, "title" | "titleIcon" | "titleTag">) => {
  // Ant's `<Text ellipsis={{ tooltip }}>` would normally cover this, but its
  // overflow detection doesn't fire reliably inside the drawer's animated
  // mount path, so we drive the tooltip from a manual ResizeObserver.
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
      {titleIcon && <span className="flex-none">{titleIcon}</span>}
      <Tooltip title={isTruncated ? title : null}>
        <span ref={titleRef} className="grow truncate">
          {title}
        </span>
      </Tooltip>
      {titleTag && <Tag {...titleTag} className="flex-none" />}
    </Flex>
  );
};

export default DetailsDrawerTitle;
