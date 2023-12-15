import {
  Badge,
  Box,
  Button,
  Checkbox,
  CheckboxGroup,
  Flex,
  Switch,
  Text,
  VStack,
} from "@fidesui/react";

import QuestionTooltip from "~/features/common/QuestionTooltip";
import { Location } from "~/types/api";

const LocationPickerCard = ({
  title,
  locations,
}: {
  title: string;
  locations: Location[];
}) => (
  <Box
    p={4}
    display="flex"
    alignItems="flex-start"
    gap="4px"
    borderRadius="4px"
    boxShadow="0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)"
    width="363px"
    fontSize="sm"
  >
    <VStack alignItems="flex-start" spacing={3} width="100%">
      <Flex justifyContent="space-between" width="100%">
        <Flex fontSize="md" textTransform="capitalize" fontWeight="semibold">
          <Checkbox isChecked={false} size="md" mr="2" />
          {title}
        </Flex>

        <Flex alignItems="center" gap="8px">
          <Switch isChecked={false} size="sm" />
          <Text>Regulated</Text>
          <QuestionTooltip />
        </Flex>
      </Flex>
      {/* {showBadge && ( */}
      <Badge colorScheme="purple" variant="solid" width="fit-content">
        X selected
      </Badge>
      {/* )} */}

      <Box paddingLeft="6" fontSize="sm">
        <CheckboxGroup colorScheme="complimentary">
          {locations.map((location) => (
            <Flex key={location.id} alignItems="center" gap="8px">
              <Checkbox isChecked={location.selected} size="md" />
              <Text fontWeight="500">{location.name}</Text>
            </Flex>
          ))}
        </CheckboxGroup>
      </Box>
      <Button size="xs" variant="ghost">
        View more
      </Button>
    </VStack>
  </Box>
);

export default LocationPickerCard;
