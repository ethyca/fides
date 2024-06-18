import { Flex, Spinner, SpinnerProps } from "fidesui";

const FidesSpinner = ({ ...props }: SpinnerProps) => (
  <Flex boxSize="full" align="center" justify="center">
    <Spinner color="primary" {...props} />
  </Flex>
);

export default FidesSpinner;
