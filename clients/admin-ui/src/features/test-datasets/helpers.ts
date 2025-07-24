export const removeNulls = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map((item) => removeNulls(item)).filter((item) => item !== null);
  }
  if (obj && typeof obj === "object") {
    return Object.fromEntries(
      Object.entries(obj)
        .map(([key, value]) => [key, removeNulls(value)])
        .filter(([, value]) => value !== null),
    );
  }
  return obj;
};
