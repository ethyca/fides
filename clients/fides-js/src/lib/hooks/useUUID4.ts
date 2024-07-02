import { useState } from "preact/hooks";
import { v4 as uuidv4 } from "uuid";

/**
 * Custom hook that generates a UUIDv4.
 * The returned value stays the same for the lifetime of the component.
 * @returns The generated UUIDv4.
 */
const useUUID4 = () => {
  const [uuid] = useState<string>(uuidv4());

  return uuid;
};
export default useUUID4;
