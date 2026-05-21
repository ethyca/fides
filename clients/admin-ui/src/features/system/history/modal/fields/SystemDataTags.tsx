import classNames from "classnames";
import { Flex, Tag, Typography } from "fidesui";
import _ from "lodash";
import React, { useEffect, useRef, useState } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";
import styles from "./SystemDataField.module.scss";

interface SystemDataTagsProps {
  label: string;
  tooltip?: string | null;
  name: string;
}

type TagValue = string | { fides_key: string };

const SystemDataTags = ({ label, tooltip, ...props }: SystemDataTagsProps) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const value =
    (_.get(selectedHistory?.[formType], props.name) as TagValue[]) ?? [];

  const contentRef = useRef<HTMLDivElement | null>(null);
  const [height, setHeight] = useState<number | null>(null);
  const [longestValue, setLongestValue] = useState<TagValue[]>([]);
  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue =
      (_.get(selectedHistory?.before, props.name) as TagValue[]) || [];
    const afterValue =
      (_.get(selectedHistory?.after, props.name) as TagValue[]) || [];

    setShouldHighlight(!_.isEqual(beforeValue, afterValue));

    setLongestValue(
      beforeValue.length > afterValue.length ? beforeValue : afterValue,
    );
  }, [selectedHistory, props.name]);

  useEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.offsetHeight);
    }
  }, [longestValue]);

  return (
    <div
      className={classNames("px-4 py-3", styles.cell, {
        [styles.highlightBefore]: shouldHighlight && formType === "before",
        [styles.highlightAfter]: shouldHighlight && formType === "after",
      })}
    >
      <Flex vertical align="flex-start">
        <Flex align="center" gap="small">
          <Typography.Text strong className="!text-xs">
            {label}
          </Typography.Text>
          <InfoTooltip label={tooltip} />
        </Flex>
        <Flex
          wrap="wrap"
          align="flex-start"
          ref={contentRef}
          style={{ minHeight: `${height}px` }}
        >
          {(height ? value : longestValue).map((tagValue, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <Tag key={index} color="marble" className="m-1">
              {typeof tagValue === "object" ? tagValue.fides_key : tagValue}
            </Tag>
          ))}
        </Flex>
        {formType === "before" && shouldHighlight && (
          <div className={styles.arrow}>→</div>
        )}
      </Flex>
    </div>
  );
};

export default SystemDataTags;
