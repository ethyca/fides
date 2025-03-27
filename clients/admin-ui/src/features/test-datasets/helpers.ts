export const removeNulls = (obj: any): any => {
  if (Array.isArray(obj)) {
    const filtered = obj
      .map((item) => removeNulls(item))
      .filter(
        (item) =>
          item !== null && (Array.isArray(item) ? item.length > 0 : true),
      );
    return filtered.length > 0 ? filtered : null;
  }
  if (obj && typeof obj === "object") {
    const entries = Object.entries(obj)
      .map(([key, value]) => [key, removeNulls(value)])
      .filter(
        ([, value]) =>
          value !== null && (Array.isArray(value) ? value.length > 0 : true),
      );

    return entries.length > 0 ? Object.fromEntries(entries) : null;
  }
  return obj;
};
