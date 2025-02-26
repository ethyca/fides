import { Box, BoxProps } from "fidesui";

const ConnectedCircle = ({
  connected,
  ...other
}: { connected?: boolean | null } & BoxProps) => {
  let color = "red.500";
  if (connected == null) {
    color = "gray.300";
  } else if (connected) {
    color = "green.500";
  }

  return (
    <Box
      width="12px"
      height="12px"
      borderRadius="6px"
      backgroundColor={color}
      {...other}
    />
  );
};

export default ConnectedCircle;
