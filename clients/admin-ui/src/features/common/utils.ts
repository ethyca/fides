// eslint-disable-next-line import/prefer-default-export
export function capitalize(text: string): string {
  return text.replace(/^\w/, (c) => c.toUpperCase());
}
