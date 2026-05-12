import _ from "lodash";
import React from "react";

import { DictOption } from "~/features/plus/plus.slice";
import { PrivacyDeclaration } from "~/types/api/models/PrivacyDeclaration";
import { SystemHistoryResponse } from "~/types/api/models/SystemHistoryResponse";
import { SystemResponse } from "~/types/api/models/SystemResponse";

/**
 * The backend stores system history before/after as Dict[str, Any] (JSONB).
 * The data is serialized from SystemSchema.model_dump(), split into three
 * history entry types: general fields, privacy_declarations, or data flow
 * (ingress/egress). This local type captures the known shape for type safety.
 */
interface SystemHistoryData {
  [key: string]: any;
}

/** Helper function to format date and time based on the user's locale */
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

/** A collection of mappings between backend identifiers an UI labels */
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
  after: Record<string, any>,
) => {
  const uniqueKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

  const addedFields: string[] = [];
  const removedFields: string[] = [];
  const changedFields: string[] = [];

  Array.from(uniqueKeys).forEach((originalKey) => {
    const key = getUiLabel(originalKey);
    const beforeValue = before[originalKey];
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

/** Creates a description of the given system history entry in the style of a commit message */
export const describeSystemChange = (history: SystemHistoryResponse) => {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { edited_by, created_at } = history;
  const before = history.before as SystemHistoryData;
  const after = history.after as SystemHistoryData;

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

/** Replaces system keys with system names (if available) */
export const assignSystemNames = (
  history: SystemHistoryResponse,
  systems: SystemResponse[],
): SystemHistoryResponse => {
  const transformList = (list: any[]): string[] =>
    list.map((item) => {
      const system = systems.find((s) => s.fides_key === item.fides_key);
      return system && system.name ? system.name : item.fides_key;
    });

  const modifiedBefore = { ...history.before } as SystemHistoryData;
  const modifiedAfter = { ...history.after } as SystemHistoryData;

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

/** Replaces vendor IDs with vendor names */
export const assignVendorLabels = (
  history: SystemHistoryResponse,
  dictionaryOptions: DictOption[],
): SystemHistoryResponse => {
  // Return the unmodified history if dictionaryOptions is empty
  if (_.isEmpty(dictionaryOptions)) {
    return history;
  }

  const lookupVendorLabel = (vendor_id: string, options: DictOption[]) =>
    options.find((option) => option.value === vendor_id)?.label ?? vendor_id;

  return {
    ...history,
    before: {
      ...history.before,
      vendor_id: lookupVendorLabel(
        (history.before as SystemHistoryData).vendor_id,
        dictionaryOptions,
      ),
    },
    after: {
      ...history.after,
      vendor_id: lookupVendorLabel(
        (history.after as SystemHistoryData).vendor_id,
        dictionaryOptions,
      ),
    },
  };
};

/** Modifies the privacy_declaration lists in the before and after objects to match in length */
export const alignPrivacyDeclarations = (
  history: SystemHistoryResponse,
): SystemHistoryResponse => {
  const historyBefore = history.before as SystemHistoryData;
  const historyAfter = history.after as SystemHistoryData;
  const before = historyBefore.privacy_declarations || [];
  const after = historyAfter.privacy_declarations || [];

  const allNames = new Set(
    [...before, ...after].map((item: any) => item.data_use),
  );
  const alignedBefore: PrivacyDeclaration[] = [];
  const alignedAfter: PrivacyDeclaration[] = [];

  allNames.forEach((data_use) => {
    const firstItem = before.find(
      (item: PrivacyDeclaration) => item.data_use === data_use,
    ) || {
      data_use: "",
      data_categories: [],
    };
    const secondItem = after.find(
      (item: PrivacyDeclaration) => item.data_use === data_use,
    ) || {
      data_use: "",
      data_categories: [],
    };
    alignedBefore.push(firstItem);
    alignedAfter.push(secondItem);
  });

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

/** Makes sure the before and after custom_field objects have the same keys
 * to align the rendering of the fields in the diff modal */
export const alignSystemCustomFields = (
  history: SystemHistoryResponse,
): SystemHistoryResponse => {
  const beforeCustomFields = {
    ...(history.before as SystemHistoryData).custom_fields,
  };
  const afterCustomFields = {
    ...(history.after as SystemHistoryData).custom_fields,
  };

  const allKeys = new Set([
    ...Object.keys(beforeCustomFields),
    ...Object.keys(afterCustomFields),
  ]);

  allKeys.forEach((key) => {
    if (!(key in beforeCustomFields)) {
      beforeCustomFields[key] = null;
    }
    if (!(key in afterCustomFields)) {
      afterCustomFields[key] = null;
    }
  });

  return {
    ...history,
    before: {
      ...history.before,
      custom_fields: beforeCustomFields,
    },
    after: {
      ...history.after,
      custom_fields: afterCustomFields,
    },
  };
};

/** Makes sure the custom fields object on privacy declarations have the same keys */
export const alignPrivacyDeclarationCustomFields = (
  history: SystemHistoryResponse,
): SystemHistoryResponse => {
  const histBefore = history.before as SystemHistoryData;
  const histAfter = history.after as SystemHistoryData;

  // If privacy_declarations[0].custom_fields isn't defined, return the unmodified history object
  if (
    !histBefore.privacy_declarations ||
    !histBefore.privacy_declarations[0] ||
    !histBefore.privacy_declarations[0].custom_fields
  ) {
    return history;
  }

  const beforeCustomFields = {
    ...histBefore.privacy_declarations[0].custom_fields,
  };
  const afterCustomFields =
    histAfter.privacy_declarations && histAfter.privacy_declarations[0]
      ? { ...histAfter.privacy_declarations[0].custom_fields }
      : {};

  const allKeys = new Set([
    ...Object.keys(beforeCustomFields),
    ...Object.keys(afterCustomFields),
  ]);

  allKeys.forEach((key) => {
    if (!(key in beforeCustomFields)) {
      beforeCustomFields[key] = null;
    }
    if (!(key in afterCustomFields)) {
      afterCustomFields[key] = null;
    }
  });

  return {
    ...history,
    before: {
      ...history.before,
      privacy_declarations: [
        {
          ...histBefore.privacy_declarations[0],
          custom_fields: beforeCustomFields,
        },
      ],
    },
    after: {
      ...history.after,
      privacy_declarations: [
        {
          ...histAfter.privacy_declarations[0],
          custom_fields: afterCustomFields,
        },
      ],
    },
  };
};
