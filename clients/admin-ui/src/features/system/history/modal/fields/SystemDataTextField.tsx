import classNames from "classnames";
import { Flex, Typography } from "fidesui";
import _ from "lodash";
import { useEffect, useRef, useState } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";
import styles from "./SystemDataField.module.scss";

interface SystemDataTextFieldProps {
  name: string;
  label?: string;
  tooltip?: string | null;
}

const SystemDataTextField = ({
  label,
  tooltip,
  ...props
}: SystemDataTextFieldProps) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const value =
    (_.get(selectedHistory?.[formType], props.name) as string) ?? "";

  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | null>(null);
  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue =
      (_.get(selectedHistory?.before, props.name) as string) || "";
    const afterValue =
      (_.get(selectedHistory?.after, props.name) as string) || "";

    setShouldHighlight(!_.isEqual(beforeValue, afterValue));

    const longestValue =
      beforeValue.length > afterValue.length ? beforeValue : afterValue;

    if (contentRef.current) {
      contentRef.current.textContent = longestValue;
      setHeight(contentRef.current.offsetHeight);
      contentRef.current.textContent = value;
    }
  }, [selectedHistory, props.name, value]);

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
        <Typography.Text ref={contentRef} style={{ height: `${height}px` }}>
          {value}
        </Typography.Text>
        {formType === "before" && shouldHighlight && (
          <div className={styles.arrow}>→</div>
        )}
      </Flex>
    </div>
  );
};

export default SystemDataTextField;
