export const PAGE_SIZE = 10;

export const chunkItems = <T>(items: T[]) => {
  const chunks: T[][] = [];
  for (let i = 0; i < items.length; i += PAGE_SIZE) {
    chunks.push(items.slice(i, i + PAGE_SIZE));
  }
  return chunks;
};
