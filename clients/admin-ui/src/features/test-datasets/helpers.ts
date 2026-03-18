/**
 * Build a lookup from collection name → Set of protected field paths
 * (including ancestor paths so that parent fields are also marked).
 */
export const buildProtectedPathsByCollection = (
  protectedCollectionFields: Array<{ collection: string; field: string }>,
): Map<string, Set<string>> => {
  const result = new Map<string, Set<string>>();
  protectedCollectionFields.forEach((pf) => {
    if (!result.has(pf.collection)) {
      result.set(pf.collection, new Set());
    }
    const pathSet = result.get(pf.collection)!;
    const segments = pf.field.split(".");
    segments.forEach((_, idx) => {
      pathSet.add(segments.slice(0, idx + 1).join("."));
    });
  });
  return result;
};

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
