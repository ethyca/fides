import {
  HStack,
  IconButton,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverContent,
  PopoverProps,
  PopoverTrigger,
  QuestionIcon,
  SimpleGrid,
  Text,
} from "fidesui";

import { ResourceChangeTypeIcons } from "~/features/data-discovery-and-detection/tables/ResultStatusCell";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";

export const IconKeyTip = ({ ...props }: PopoverProps) => (
  <Popover {...props} trigger="hover" placement="top">
    <PopoverTrigger>
      <IconButton
        aria-label="Help"
        icon={<QuestionIcon />}
        variant="ghost"
        size="xs"
        _hover={{ bg: "transparent" }}
        fontSize="md"
        color="gray.400"
      />
    </PopoverTrigger>
    <PopoverContent bg="black" width="auto">
      <PopoverArrow bg="black" />
      <PopoverBody>
        <Text as="h4" fontSize="xs" color="white" fontWeight="600" mb={2}>
          Activity Legend:
        </Text>
        <SimpleGrid columns={2} spacingX={4} spacingY={2}>
          {ResourceChangeTypeIcons.map(({ icon: Icon, label, color, type }) => (
            <HStack key={label}>
              <Icon
                color={color}
                boxSize={type === ResourceChangeType.CLASSIFICATION ? 3 : 2}
              />
              <Text fontSize="xs" color="white">
                {label}
              </Text>
            </HStack>
          ))}
        </SimpleGrid>
      </PopoverBody>
    </PopoverContent>
  </Popover>
);
