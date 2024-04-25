import { createIcon } from "@chakra-ui/icons";

export const CircleIcon = createIcon({
  displayName: "CircleIcon",
  viewBox: "0 0 200 200",
  path: (
    <path
      fill="currentColor"
      d="M 100, 100 m -75, 0 a 75,75 0 1,0 150,0 a 75,75 0 1,0 -150,0"
    />
  ),
});
