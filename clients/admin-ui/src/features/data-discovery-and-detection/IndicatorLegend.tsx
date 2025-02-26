import {
  Box,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverContent,
  PopoverHeader,
  PopoverTrigger,
  QuestionIcon,
  SimpleGrid,
} from "fidesui";

import {
  AdditionIndicator,
  ChangeIndicator,
  ClassificationIndicator,
  MonitoredIndicator,
  MutedIndicator,
  RemovalIndicator,
} from "~/features/data-discovery-and-detection/statusIndicators";

const IconLegendTooltip = () => (
  <Popover isLazy trigger="hover">
    <PopoverTrigger>
      <QuestionIcon color="gray.400" />
    </PopoverTrigger>
    <PopoverContent
      bgColor="gray.800"
      color="white"
      fontSize="sm"
      w="auto"
      border="none"
    >
      <PopoverHeader fontWeight="semibold" border="none" pb={0}>
        Activity legend:
      </PopoverHeader>
      <PopoverArrow bgColor="gray.800" />
      <PopoverBody border="none">
        <SimpleGrid columns={2} spacing={2}>
          <Box>
            <ChangeIndicator /> Change detected
          </Box>
          <Box>
            <ClassificationIndicator /> Data labeled
          </Box>
          <Box>
            <MonitoredIndicator /> Monitoring
          </Box>
          <Box>
            <AdditionIndicator /> Addition detected
          </Box>
          <Box>
            <MutedIndicator /> Unmonitored
          </Box>
          <Box>
            <RemovalIndicator /> Removal detected
          </Box>
        </SimpleGrid>
      </PopoverBody>
    </PopoverContent>
  </Popover>
);

export default IconLegendTooltip;
