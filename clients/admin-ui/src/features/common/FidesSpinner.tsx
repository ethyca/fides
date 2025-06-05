import { Flex, Spinner, SpinnerProps } from "fidesui";

interface FidesSpinnerProps extends SpinnerProps {
  alignment?: "center" | "start" | "end";
}

const FidesSpinner = ({
  alignment = "center",
  ...props
}: FidesSpinnerProps) => (
  <Flex boxSize="full" align="center" justify={alignment}>
    <Spinner color="primary" {...props} />
  </Flex>
);

export default FidesSpinner;
