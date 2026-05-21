import { Card } from "fidesui";
import _ from "lodash";
import React from "react";

import { useSelectedHistory } from "./SelectedHistoryContext";

const SystemDataGroup = ({
  heading,
  children,
}: {
  heading: string;
  children?: React.ReactNode;
}) => {
  const { selectedHistory } = useSelectedHistory();
  const childArray = React.Children.toArray(children);

  // Filter children based on whether their name prop exists in before or after of selectedHistory
  const filteredChildren = childArray.filter((child) => {
    if (React.isValidElement<{ name?: string }>(child) && child.props.name) {
      const { name } = child.props;
      const beforeValue = _.get(selectedHistory?.before, name);
      const afterValue = _.get(selectedHistory?.after, name);
      const isBeforeValueEmpty =
        typeof beforeValue === "boolean" || typeof beforeValue === "number"
          ? false
          : _.isEmpty(beforeValue);
      const isAfterValueEmpty =
        typeof afterValue === "boolean" || typeof afterValue === "number"
          ? false
          : _.isEmpty(afterValue);

      return !isBeforeValueEmpty || !isAfterValueEmpty;
    }
    return false;
  });

  if (filteredChildren.length === 0) {
    return null;
  }

  return (
    <Card
      title={heading}
      variant="outlined"
      className="mt-6 max-w-[720px] overflow-visible"
      styles={{
        body: { padding: 0 },
        header: { padding: "16px" },
      }}
    >
      {filteredChildren}
    </Card>
  );
};

export default SystemDataGroup;
