import _ from "lodash";
import React from "react";

import { DictOption } from "~/features/plus/plus.slice";
import { PrivacyDeclaration } from "~/types/api/models/PrivacyDeclaration";
import { SystemHistoryResponse } from "~/types/api/models/SystemHistoryResponse";
import { SystemResponse } from "~/types/api/models/SystemResponse";

// Helper function to format date and time
export const formatDateAndTime = (dateString: string) => {
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

export function alignArrays(
  before: PrivacyDeclaration[],
  after: PrivacyDeclaration[]
) {
  const allNames = new Set([...before, ...after].map((item) => item.data_use));
  const alignedBefore: PrivacyDeclaration[] = [];
  const alignedAfter: PrivacyDeclaration[] = [];

  allNames.forEach((data_use) => {
    const firstItem = before.find((item) => item.data_use === data_use) || {
      data_use: "",
      data_categories: [],
    };
    const secondItem = after.find((item) => item.data_use === data_use) || {
      data_use: "",
      data_categories: [],
    };
    alignedBefore.push(firstItem);
    alignedAfter.push(secondItem);
  });

  return [alignedBefore, alignedAfter];
}

const lookupVendorLabel = (vendor_id: string, options: DictOption[]) =>
  options.find((option) => option.value === vendor_id)?.label ?? vendor_id;

export const getUiLabel = (key: string): string => {
  const keyMapping: Record<string, string> = {
    privacy_declarations: "data uses",
    ingress: "sources",
    egress: "destinations",
  };

  return keyMapping[key] || key;
};

/** Determines if a field was added, modified, or removed as part of modification */
const categorizeFieldModifications = (
  before: Record<string, any>,
  after: Record<string, any>
) => {
  const uniqueKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

  const addedFields: string[] = [];
  const removedFields: string[] = [];
  const changedFields: string[] = [];

  Array.from(uniqueKeys).forEach((originalKey) => {
    const key = getUiLabel(originalKey);
    // @ts-ignore
    const beforeValue = before[originalKey];
    // @ts-ignore
    const afterValue = after[originalKey];

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

  return { addedFields, removedFields, changedFields };
};

export const describeSystemChange = (history: SystemHistoryResponse) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { edited_by, before, after, created_at } = history;

  let addedFields: string[] = [];
  let removedFields: string[] = [];
  let changedFields: string[] = [];

  // if the history contains custom fields, it won't have the main fields
  // so we can just process the custom_fields object
  if (before.custom_fields || after.custom_fields) {
    ({ addedFields, removedFields, changedFields } =
      categorizeFieldModifications(before.custom_fields, after.custom_fields));
  } else {
    // process the main fields
    ({ addedFields, removedFields, changedFields } =
      categorizeFieldModifications(before, after));
  }

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
      <b>{edited_by}</b> {descriptionList} on {formattedDate} at {formattedTime}
    </>
  );
};

export const assignSystemNames = (
  history: SystemHistoryResponse,
  systems: SystemResponse[]
): SystemHistoryResponse => {
  const transformList = (list: any[]): string[] =>
    list.map((item) => {
      const system = systems.find((s) => s.fides_key === item.fides_key);
      return system && system.name ? system.name : item.fides_key;
    });

  const modifiedBefore = { ...history.before };
  const modifiedAfter = { ...history.after };

  if (modifiedBefore.ingress) {
    modifiedBefore.ingress = transformList(modifiedBefore.ingress);
  }

  if (modifiedBefore.egress) {
    modifiedBefore.egress = transformList(modifiedBefore.egress);
  }

  if (modifiedAfter.ingress) {
    modifiedAfter.ingress = transformList(modifiedAfter.ingress);
  }

  if (modifiedAfter && modifiedAfter.egress) {
    modifiedAfter.egress = transformList(modifiedAfter.egress);
  }

  return { ...history, before: modifiedBefore, after: modifiedAfter };
};

export const assignVendorLabels = (
  history: SystemHistoryResponse,
  dictionaryOptions: DictOption[]
): SystemHistoryResponse => {
  // Return the unmodified history if dictionaryOptions is empty
  if (_.isEmpty(dictionaryOptions)) {
    return history;
  }

  return {
    ...history,
    before: {
      ...history.before,
      vendor_id: lookupVendorLabel(history.before.vendor_id, dictionaryOptions),
    },
    after: {
      ...history.after,
      vendor_id: lookupVendorLabel(history.after.vendor_id, dictionaryOptions),
    },
  };
};

export const alignPrivacyDeclarations = (
  history: SystemHistoryResponse
): SystemHistoryResponse => {
  const beforePrivacyDeclarations = history.before.privacy_declarations || [];
  const afterPrivacyDeclarations = history.after.privacy_declarations || [];
  const [alignedBefore, alignedAfter] = alignArrays(
    beforePrivacyDeclarations,
    afterPrivacyDeclarations
  );

  return {
    ...history,
    before: {
      ...history.before,
      privacy_declarations: alignedBefore,
    },
    after: {
      ...history.after,
      privacy_declarations: alignedAfter,
    },
  };
};
