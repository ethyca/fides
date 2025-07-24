import {
  AntSpace as Space,
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
          <Space>
            <ChangeIndicator />
            <div>Change detected</div>
          </Space>
          <Space>
            <ClassificationIndicator />
            <div>Data labeled</div>
          </Space>
          <Space>
            <MonitoredIndicator />
            <div>Monitoring</div>
          </Space>
          <Space>
            <AdditionIndicator />
            <div>Addition detected</div>
          </Space>
          <Space>
            <MutedIndicator />
            <div>Unmonitored</div>
          </Space>
          <Space>
            <RemovalIndicator />
            <div>Removal detected</div>
          </Space>
        </SimpleGrid>
      </PopoverBody>
    </PopoverContent>
  </Popover>
);

export default IconLegendTooltip;
