import classNames from "classnames";
import { Flex, Tag, Typography } from "fidesui";
import _ from "lodash";
import { useEffect, useState } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";
import styles from "./SystemDataField.module.scss";

interface SystemDataSwitchProps {
  name: string;
  label?: string;
  tooltip?: string | null;
}

const SystemDataSwitch = ({
  label,
  tooltip,
  ...props
}: SystemDataSwitchProps) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const value = _.get(selectedHistory?.[formType], props.name) as
    | boolean
    | undefined;

  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name);
    const afterValue = _.get(selectedHistory?.after, props.name);

    setShouldHighlight(beforeValue !== afterValue);
  }, [selectedHistory, props.name, value]);

  return (
    <div
      className={classNames("px-4 py-3", styles.cell, {
        [styles.highlightBefore]: shouldHighlight && formType === "before",
        [styles.highlightAfter]: shouldHighlight && formType === "after",
      })}
    >
      <Flex vertical align="flex-start" className="min-h-[46px]">
        <Flex align="center" gap="small">
          <Typography.Text strong className="!text-xs">
            {label}
          </Typography.Text>
          <InfoTooltip label={tooltip} />
        </Flex>
        {value !== undefined && (
          <Tag color="marble" className="m-1">
            {value ? "YES" : "NO"}
          </Tag>
        )}
        {formType === "before" && shouldHighlight && (
          <div className={styles.arrow}>→</div>
        )}
      </Flex>
    </div>
  );
};

export default SystemDataSwitch;
