export default function sizeOf(searchParams: URLSearchParams) {
  return Array.from(searchParams).length;
}
