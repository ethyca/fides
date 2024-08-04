import {
  Badge,
  Box,
  Button,
  chakra,
  Heading,
  Stack,
  StepperCircleCheckmarkIcon,
  StepperCircleIcon,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "fidesui";
import { useRouter } from "next/router";

import { useAppDispatch } from "~/app/hooks";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import { System } from "~/types/api";

import { setActiveSystem } from "../system";

interface Props {
  systemInReview: System;
  systemsForReview: System[];
  onAddNextSystem: () => void;
}
const SuccessPage = ({
  systemInReview,
  systemsForReview,
  onAddNextSystem,
}: Props) => {
  const systemName = systemInReview.name ?? systemInReview.fides_key;
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();

  // Systems are reviewed in order, so a lower index means that system has been reviewed
  // and a higher index means they'll reviewed after hitting "next".
  const systemInReviewIndex = systemsForReview.findIndex(
    (s) => s.fides_key === systemInReview.fides_key,
  );

  const onFinish = () => {
    dispatch(setActiveSystem(undefined));
    router.push(systemOrDatamapRoute);
  };

  return (
    <chakra.form w="100%">
      <Stack spacing={10}>
        <Heading
          as="h3"
          color="green.500"
          size="lg"
          data-testid="success-page-heading"
        >
          <Badge
            fontSize="16px"
            margin="10px"
            padding="10px"
            variant="solid"
            colorScheme="green"
          >
            Success
          </Badge>
          {systemName} successfully registered!
        </Heading>
        <Text>{systemName} has been successfully added to the registry!</Text>
        <TableContainer>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th pl={0}>System Name</Th>
              </Tr>
            </Thead>
            <Tbody>
              {systemsForReview.map((s, i) => (
                <Tr key={`${s.fides_key}-tr`}>
                  <Td
                    color={i === systemInReviewIndex ? "green.500" : undefined}
                    pl={0}
                  >
                    {s.name}
                  </Td>
                  <Td>
                    {i <= systemInReviewIndex ? (
                      <StepperCircleCheckmarkIcon
                        boxSize={5}
                        data-testid="system-reviewed"
                      />
                    ) : (
                      <StepperCircleIcon
                        boxSize={5}
                        data-testid="system-needs-review"
                      />
                    )}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>

        <Text>You can continue to add more systems now or finish.</Text>

        <Box>
          <Button
            onClick={onAddNextSystem}
            mr={2}
            size="sm"
            variant="outline"
            data-testid="add-next-system-btn"
          >
            Add system manually
          </Button>

          <Button
            onClick={onFinish}
            colorScheme="primary"
            size="sm"
            data-testid="finish-btn"
          >
            Finish
          </Button>
        </Box>
      </Stack>
    </chakra.form>
  );
};
export default SuccessPage;
