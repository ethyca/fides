export const zip = <L, R>(
  left: Record<string, L>,
  right: Record<string, R>,
) => {
  const keys = [...Object.keys(left), ...Object.keys(right)];

  return Object.fromEntries(
    keys.map((key): [string, [L | undefined, R | undefined]] => {
      return [key, [left?.[key], right?.[key]]];
    }),
  );
};

export const mappedZip = <L, R, M>(
  left: Record<string, L>,
  right: Record<string, R>,
  func: (l?: L, r?: R) => M,
): Record<string, M> => {
  const keys = [...Object.keys(left), ...Object.keys(right)];

  return Object.fromEntries(
    keys.map((key): [string, M] => {
      return [key, func(left?.[key], right?.[key])];
    }),
  );
};
