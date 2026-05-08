import { useState } from "preact/hooks";

/**
 * Custom hook that generates a UUIDv4.
 * The returned value stays the same for the lifetime of the component.
 * @returns The generated UUIDv4.
 */
const useUUID4 = () => {
  const [uuid] = useState<string>(() => crypto.randomUUID());

  return uuid;
};
export default useUUID4;
