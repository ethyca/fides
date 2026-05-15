import { useState } from "preact/hooks";

/**
 * Custom hook that generates a UUID.
 * The returned value stays the same for the lifetime of the component.
 * @returns The generated UUID.
 */
const useUUID4 = () => {
  const [uuid] = useState<string>(() => crypto.randomUUID());

  return uuid;
};
export default useUUID4;
