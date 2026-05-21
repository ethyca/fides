import type { UploadFile } from "fidesui";

import type { FormValues } from "~/types/forms";

/**
 * Upload a single file to the privacy request attachment endpoint.
 * Returns the attachment ID on success.
 */
export const uploadFile = async (
  file: File,
  apiUrl: string,
  context: { propertyId: string; policyKey: string; fieldName: string },
): Promise<string> => {
  const formData = new FormData();
  formData.append("file", file);
  if (context.propertyId) {
    formData.append("property_id", context.propertyId);
  }
  formData.append("policy_key", context.policyKey);
  formData.append("field_name", context.fieldName);

  const response = await fetch(`${apiUrl}/privacy-request/attachment`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data?.detail || `File upload failed (${response.status})`);
  }

  const data = await response.json();
  return data.id;
};

/**
 * Upload all files for a single field and return their attachment IDs.
 * Uploads sequentially to respect rate limits.
 */
export const uploadFieldFiles = async (
  fileList: UploadFile[],
  apiUrl: string,
  context: { propertyId: string; policyKey: string; fieldName: string },
): Promise<string[]> => {
  const filesToUpload = fileList
    .filter((f) => f.originFileObj)
    .map((f) => f.originFileObj as File);

  // Sequential uploads to respect rate limits
  const ids: string[] = [];
  // eslint-disable-next-line no-restricted-syntax
  for (const file of filesToUpload) {
    // eslint-disable-next-line no-await-in-loop
    const id = await uploadFile(file, apiUrl, context);
    ids.push(id);
  }
  return ids;
};

/**
 * Upload all files for file-type custom fields and return a map of
 * field key → attachment ID array.
 */
export const uploadAllFiles = async (
  values: FormValues,
  fields: Record<string, { field_type?: string | null }>,
  apiUrl: string,
  context: { propertyId: string; policyKey: string },
): Promise<Record<string, string[]>> => {
  const fileFieldKeys = Object.entries(fields)
    .filter(([, field]) => field.field_type === "file")
    .map(([key]) => key);

  const entries = await Promise.all(
    fileFieldKeys
      .filter((key) => {
        const fileList = values[key] as UploadFile[];
        return fileList && fileList.length > 0;
      })
      .map(async (key) => {
        const fileList = values[key] as UploadFile[];
        const ids = await uploadFieldFiles(fileList, apiUrl, {
          ...context,
          fieldName: key,
        });
        return [key, ids] as [string, string[]];
      }),
  );

  return Object.fromEntries(entries.filter(([, ids]) => ids.length > 0));
};
