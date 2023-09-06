import { Table, Tbody, Td, Thead, Tr } from "@fidesui/react";
import _ from "lodash";
import React from "react";

import { useGetSystemHistoryQuery } from "~/features/plus/plus.slice";
import { SystemHistoryResponse } from "~/types/api/models/SystemHistoryResponse";
import { SystemResponse } from "~/types/api/models/SystemResponse";

interface Props {
  system: SystemResponse;
}

// Helper function to format date and time
const formatDateAndTime = (dateString: string) => {
  const date = new Date(dateString);
  const userLocale = navigator.language;

  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZoneName: "short",
  };

  const dateOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  const formattedTime = date.toLocaleTimeString(userLocale, timeOptions);
  const formattedDate = date.toLocaleDateString(userLocale, dateOptions);

  return { formattedTime, formattedDate };
};

const SystemHistoryTable = ({ system }: Props) => {
  // Fetch system history data
  const { data } = useGetSystemHistoryQuery({
    system_key: system.fides_key,
  });

  const systemHistories = data?.items || [];

  const describeSystemChange = (history: SystemHistoryResponse) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { edited_by, before, after, created_at } = history;

    const uniqueKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

    const addedFields: string[] = [];
    const removedFields: string[] = [];
    const changedFields: string[] = [];

    Array.from(uniqueKeys).forEach((key) => {
      // @ts-ignore
      const beforeValue = before[key];
      // @ts-ignore
      const afterValue = after[key];

      // Handle booleans separately
      if (typeof beforeValue === "boolean" || typeof afterValue === "boolean") {
        if (beforeValue !== afterValue) {
          changedFields.push(key);
        }
        return;
      }

      // Handle numbers separately
      if (typeof beforeValue === "number" || typeof afterValue === "number") {
        if (beforeValue !== afterValue) {
          changedFields.push(key);
        }
        return;
      }

      // If both values are null or empty, skip
      if (
        (_.isNil(beforeValue) || _.isEmpty(beforeValue)) &&
        (_.isNil(afterValue) || _.isEmpty(afterValue))
      ) {
        return;
      }

      // For all other types
      if (!_.isEqual(beforeValue, afterValue)) {
        if (_.isNil(beforeValue) || _.isEmpty(beforeValue)) {
          addedFields.push(key);
        } else if (_.isNil(afterValue) || _.isEmpty(afterValue)) {
          removedFields.push(key);
        } else {
          changedFields.push(key);
        }
      }
    });

    const changeDescriptions: Array<[string, JSX.Element]> = [];

    if (addedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["added ", <b>{addedFields.join(", ")}</b>]);
    }

    if (removedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["removed ", <b>{removedFields.join(", ")}</b>]);
    }

    if (changedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["changed ", <b>{changedFields.join(", ")}</b>]);
    }

    if (changeDescriptions.length === 0) {
      return null;
    }

    const lastDescription = changeDescriptions.pop();

    const descriptionList =
      changeDescriptions.length > 0 ? (
        <>
          {changeDescriptions.map((desc, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <React.Fragment key={i}>
              {desc}
              {i < changeDescriptions.length - 1 ? ", " : ""}
            </React.Fragment>
          ))}
          {changeDescriptions.length >= 2 ? ", and " : " and "}
          {lastDescription}
        </>
      ) : (
        lastDescription
      );

    const { formattedTime, formattedDate } = formatDateAndTime(created_at);

    return (
      <>
        <b>{edited_by}</b> {descriptionList} on {formattedDate} at{" "}
        {formattedTime}
      </>
    );
  };

  const { formattedTime, formattedDate } = formatDateAndTime(system.created_at);

  return (
    <Table style={{ marginLeft: "24px" }}>
      <Thead>
        <Tr>
          <Td
            style={{
              paddingTop: 16,
              paddingBottom: 16,
              paddingLeft: 16,
              fontSize: 12,
              borderTop: "1px solid #E2E8F0",
              borderLeft: "1px solid #E2E8F0",
              borderRight: "1px solid #E2E8F0",
              background: "#F7FAFC",
            }}
          >
            System created
            {system.created_by && (
              <>
                {" "}
                by <b>{system.created_by}</b>{" "}
              </>
            )}{" "}
            on {formattedDate} at {formattedTime}
          </Td>
        </Tr>
      </Thead>
      <Tbody>
        {systemHistories.map(
          (history: SystemHistoryResponse, index: number) => {
            const description = describeSystemChange(history);
            return (
              <Tr
                // eslint-disable-next-line react/no-array-index-key
                key={index}
              >
                <Td
                  style={{
                    paddingTop: 10,
                    paddingBottom: 10,
                    paddingLeft: 16,
                    fontSize: 12,
                    borderLeft: "1px solid #E2E8F0",
                    borderRight: "1px solid #E2E8F0",
                  }}
                >
                  {description}
                </Td>
              </Tr>
            );
          }
        )}
      </Tbody>
    </Table>
  );
};

export default SystemHistoryTable;
