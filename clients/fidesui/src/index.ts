import { CustomTypography } from "./hoc/CustomTypography";

/**
 * @deprecated Chakra UI components are deprecated and will be removed in a future release.
 * Please use Ant Design components instead.
 */
export {
  chakra,
  // Disclosure
  Accordion as ChakraAccordion,
  AccordionButton as ChakraAccordionButton,
  AccordionIcon as ChakraAccordionIcon,
  AccordionItem as ChakraAccordionItem,
  AccordionPanel as ChakraAccordionPanel,
  // Feedback
  Alert as ChakraAlert,
  AlertDescription as ChakraAlertDescription,
  AlertDialog as ChakraAlertDialog,
  AlertDialogBody as ChakraAlertDialogBody,
  AlertDialogContent as ChakraAlertDialogContent,
  AlertDialogFooter as ChakraAlertDialogFooter,
  AlertDialogHeader as ChakraAlertDialogHeader,
  AlertDialogOverlay as ChakraAlertDialogOverlay,
  AlertIcon as ChakraAlertIcon,
  AlertTitle as ChakraAlertTitle,
  // Layout
  Box as ChakraBox,
  // Forms
  Button as ChakraButton,
  ButtonGroup as ChakraButtonGroup,
  Center as ChakraCenter,
  Checkbox as ChakraCheckbox,
  CheckboxGroup as ChakraCheckboxGroup,
  // Other
  CloseButton as ChakraCloseButton,
  Code as ChakraCode,
  Collapse as ChakraCollapse,
  Container as ChakraContainer,
  Divider as ChakraDivider,
  Drawer as ChakraDrawer,
  DrawerBody as ChakraDrawerBody,
  DrawerCloseButton as ChakraDrawerCloseButton,
  DrawerContent as ChakraDrawerContent,
  DrawerFooter as ChakraDrawerFooter,
  DrawerHeader as ChakraDrawerHeader,
  DrawerOverlay as ChakraDrawerOverlay,
  Flex as ChakraFlex,
  FormControl as ChakraFormControl,
  FormErrorMessage as ChakraFormErrorMessage,
  FormHelperText as ChakraFormHelperText,
  FormLabel as ChakraFormLabel,
  // Utilities
  forwardRef as chakraForwardRef,
  Grid as ChakraGrid,
  Heading as ChakraHeading,
  HStack as ChakraHStack,
  IconButton as ChakraIconButton,
  // Data Display
  Image as ChakraImage,
  Input as ChakraInput,
  InputGroup as ChakraInputGroup,
  InputLeftElement as ChakraInputLeftElement,
  InputRightElement as ChakraInputRightElement,
  // Navigation
  Link as ChakraLink,
  LinkBox as ChakraLinkBox,
  LinkOverlay as ChakraLinkOverlay,
  List as ChakraList,
  ListIcon as ChakraListIcon,
  ListItem as ChakraListItem,
  Menu as ChakraMenu,
  MenuButton as ChakraMenuButton,
  MenuDivider as ChakraMenuDivider,
  MenuItem as ChakraMenuItem,
  MenuItemOption as ChakraMenuItemOption,
  MenuList as ChakraMenuList,
  MenuOptionGroup as ChakraMenuOptionGroup,
  // Overlay
  Modal as ChakraModal,
  ModalBody as ChakraModalBody,
  ModalCloseButton as ChakraModalCloseButton,
  ModalContent as ChakraModalContent,
  ModalFooter as ChakraModalFooter,
  ModalHeader as ChakraModalHeader,
  ModalOverlay as ChakraModalOverlay,
  NumberDecrementStepper as ChakraNumberDecrementStepper,
  NumberIncrementStepper as ChakraNumberIncrementStepper,
  NumberInput as ChakraNumberInput,
  NumberInputField as ChakraNumberInputField,
  NumberInputStepper as ChakraNumberInputStepper,
  OrderedList as ChakraOrderedList,
  Portal as ChakraPortal,
  SimpleGrid as ChakraSimpleGrid,
  Skeleton as ChakraSkeleton,
  Spacer as ChakraSpacer,
  Spinner as ChakraSpinner,
  Stack as ChakraStack,
  StackDivider as ChakraStackDivider,
  Table as ChakraTable,
  TableContainer as ChakraTableContainer,
  Tag as ChakraTag,
  TagCloseButton as ChakraTagCloseButton,
  TagLabel as ChakraTagLabel,
  Tbody as ChakraTbody,
  Td as ChakraTd,
  // Typography
  Text as ChakraText,
  Textarea as ChakraTextarea,
  Tfoot as ChakraTfoot,
  Th as ChakraTh,
  Thead as ChakraThead,
  Tr as ChakraTr,
  UnorderedList as ChakraUnorderedList,
  VStack as ChakraVStack,
  Wrap as ChakraWrap,
  createStandaloneToast as createChakraStandaloneToast,
  getCSSVar as getChakraCSSVar,
} from "@chakra-ui/react";

/**
 * @deprecated Chakra UI hooks are deprecated and will be removed in a future release.
 * Please use Ant Design hooks instead.
 */
export {
  useClipboard as useChakraClipboard,
  useDisclosure as useChakraDisclosure,
  useFormControlContext as useChakraFormControlContext,
  usePrefersReducedMotion as useChakraPrefersReducedMotion,
  useToast as useChakraToast,
} from "@chakra-ui/react";

/**
 * @deprecated Chakra UI types are deprecated and will be removed in a future release.
 * Please use Ant Design types instead.
 */
export type {
  AccordionItemProps as ChakraAccordionItemProps,
  BoxProps as ChakraBoxProps,
  ButtonProps as ChakraButtonProps,
  ChakraProps as ChakraChakraProps,
  CheckboxProps as ChakraCheckboxProps,
  FlexProps as ChakraFlexProps,
  FormErrorMessageProps as ChakraFormErrorMessageProps,
  FormLabelProps as ChakraFormLabelProps,
  HeadingProps as ChakraHeadingProps,
  HTMLChakraProps as ChakraHTMLChakraProps,
  InputProps as ChakraInputProps,
  LinkProps as ChakraLinkProps,
  MenuButtonProps as ChakraMenuButtonProps,
  ModalContentProps as ChakraModalContentProps,
  ModalProps as ChakraModalProps,
  SpinnerProps as ChakraSpinnerProps,
  StackProps as ChakraStackProps,
  TableCellProps as ChakraTableCellProps,
  TableHeadProps as ChakraTableHeadProps,
  TextareaProps as ChakraTextareaProps,
  TextProps as ChakraTextProps,
  UseDisclosureReturn as ChakraUseDisclosureReturn,
  UseToastOptions as ChakraUseToastOptions,
} from "@chakra-ui/react";

/**
 * @deprecated Chakra UI utils are deprecated and will be removed in a future release.
 */
export { isNumeric as isChakraNumeric } from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { DisplayValueType } from "@rc-component/select/lib/interface";
export type { ThemeConfig } from "antd/es";
export type {
  FilterValue,
  SorterResult,
  TablePaginationConfig,
} from "antd/es/table/interface";
export type {
  BadgeProps,
  ButtonProps,
  CheckboxProps,
  CollapseProps,
  DatePickerProps,
  DropdownProps,
  FlexProps,
  FormInstance,
  FormItemProps,
  FormProps,
  GetProps,
  InputProps as InputPropsOriginal,
  InputRef,
  MenuProps,
  ModalProps,
  PopoverProps,
  ProgressProps,
  RadioChangeEvent,
  RadioGroupProps,
  SelectProps,
  SwitchProps,
  TableProps,
  TabsProps,
  TooltipProps,
  TreeDataNode,
  TreeProps,
  UploadFile,
  UploadProps,
} from "antd/lib";
export {
  AutoComplete,
  Badge,
  Breadcrumb,
  Button,
  Cascader,
  Checkbox,
  Col,
  Collapse,
  ConfigProvider,
  DatePicker,
  Descriptions,
  Divider,
  Empty,
  Flex,
  Form,
  Image,
  InputNumber,
  Layout,
  Menu,
  Modal,
  notification,
  Pagination,
  Popconfirm,
  Popover,
  Progress,
  Radio,
  Result,
  Row,
  Segmented,
  Skeleton,
  Space,
  Splitter,
  Steps,
  Switch,
  // the HOC CustomSpin is incompatible with a handful of usages for loading
  // states on Chakra tables, so we re-export the base Spin.
  // TODO: remove when all FidesTableV2s are migrated to Ant
  Spin as TableSpinner,
  Tabs,
  TimePicker,
  Tree,
  TreeSelect,
  Upload,
} from "antd/lib";
export type {
  BreadcrumbItemType,
  BreadcrumbProps,
} from "antd/lib/breadcrumb/Breadcrumb";
export type { ListItemProps } from "antd/lib/list";
export type { BaseOptionType, DefaultOptionType } from "antd/lib/select";
export type { UploadChangeParam } from "antd/lib/upload";

// Higher-order components
export type {
  CustomAlertProps as AlertProps,
  CustomAvatarProps as AvatarProps,
  CustomCardProps as CardProps,
  DrawerProps,
  ICustomMultiSelectProps,
  ICustomSelectProps,
  CustomInputProps as InputProps,
  CustomSpinProps as SpinProps,
  CustomStatisticProps as StatisticProps,
  StatisticTrend,
} from "./hoc";
export {
  CustomAlert as Alert,
  CustomAvatar as Avatar,
  CustomCard as Card,
  CopyTooltip,
  CustomDateRangePicker as DateRangePicker,
  CustomDrawer as Drawer,
  CustomDropdown as Dropdown,
  CustomInput as Input,
  CustomList as List,
  CustomSelect as Select,
  CustomSpin as Spin,
  CustomStatistic as Statistic,
  CustomTable as Table,
  CustomTag as Tag,
  CustomTooltip as Tooltip,
  CustomTypography as Typography,
} from "./hoc";
export type {
  CustomListProps as ListProps,
  RowSelection,
} from "./hoc/CustomList";
export type { CustomColumnsType as ColumnsType } from "./hoc/CustomTable";
export type { CustomTagProps as TagProps } from "./hoc/CustomTag";
export { CUSTOM_TAG_COLOR } from "./hoc/CustomTag";
export { LIST_HOTKEYS } from "./hooks/useListHotkeys";

// Export utils
export * from "./components/data-display/filter.utils";
export * from "./components/data-display/location.utils";
export { isoCodesToOptions } from "./components/data-entry/LocationSelect";

// Export ISO 3166 data for location selection
export type { ISO31661Entry, ISO31662Entry } from "iso-3166";
export { iso31661, iso31662 } from "iso-3166";

// Export data-display components
export type {
  AreaChartDataPoint,
  AreaChartProps,
  AreaChartSeries,
} from "./components/charts/AreaChart";
export { AreaChart } from "./components/charts/AreaChart";
export type {
  BarChartDataPoint,
  BarChartProps,
} from "./components/charts/BarChart";
export { BarChart } from "./components/charts/BarChart";
export type {
  AntColorTokenKey,
  BarSize,
} from "./components/charts/chart-constants";
export {
  CHART_ANIMATION,
  CHART_GRADIENT,
  CHART_STROKE,
  CHART_TYPOGRAPHY,
} from "./components/charts/chart-constants";
export {
  DAY_MS,
  formatTimestamp,
  HOUR_MS,
} from "./components/charts/chart-utils";
export type { ChartGradientProps } from "./components/charts/ChartGradient";
export { ChartGradient } from "./components/charts/ChartGradient";
export type { ChartTextProps } from "./components/charts/ChartText";
export { ChartText } from "./components/charts/ChartText";
export type {
  DonutChartProps,
  DonutChartSegment,
  DonutChartVariant,
} from "./components/charts/DonutChart";
export { DonutChart } from "./components/charts/DonutChart";
export type {
  RadarChartDataPoint,
  RadarChartProps,
  RadarPointStatus,
} from "./components/charts/RadarChart";
export { RadarChart } from "./components/charts/RadarChart";
export { RadarTooltipContent } from "./components/charts/RadarTooltipContent";
export type { SparklineProps } from "./components/charts/Sparkline";
export { Sparkline } from "./components/charts/Sparkline";
export type {
  StackedBarChartProps,
  StackedBarSegment,
} from "./components/charts/StackedBarChart";
export { StackedBarChart } from "./components/charts/StackedBarChart";
export { XAxisTick } from "./components/charts/XAxisTick";
export type { FilterProps } from "./components/data-display/Filter";
export { Filter } from "./components/data-display/Filter";
export type { TagListProps } from "./components/data-display/TagList";
export { TagList } from "./components/data-display/TagList";

// Export animation components
export type {
  EnterExitListProps,
  ExitGridProps,
  ExpandCollapseProps,
  OpenCloseArrowProps,
} from "./components/animation";
export {
  EnterExitList,
  ExitGrid,
  ExpandCollapse,
  OpenCloseArrow,
} from "./components/animation";

// Export data-entry components
export type { LocationSelectProps } from "./components/data-entry/LocationSelect";
export { LocationSelect } from "./components/data-entry/LocationSelect";
export { SelectInline } from "./components/data-entry/SelectInline";

// Export navigation components
export { FloatingMenu } from "./components/navigation/FloatingMenu";

// Export the destructured Typography components individually
export const { Text, Title, Paragraph, Link } = CustomTypography;

/**
 * Custom Re-exports
 *
 * Icons whose names conflict with Chakra's included icons must be explicitly listed. This makes
 * typescript happy, but eslint doesn't understand.
 */
/* eslint-disable import/export */
export * from "./icons";
export {
  CarryOutOutlined,
  CheckOutlined,
  CloseOutlined,
  DownOutlined,
  PlusOutlined,
  SyncOutlined,
} from "@ant-design/icons";
/* eslint-enable import/export */

/**
 * prefixed icons from Carbon Icons
 * @example <Icons.download size={14} />
 */
export * as Icons from "./icons/carbon";
/* end prefixed icons */

export {
  FidesUIProvider,
  useMessage,
  useModal,
  useNotification,
} from "./FidesUIProvider";
export { extendTheme, theme } from "./FidesUITheme";
export { getGlobalMessageApi } from "./lib/globalMessageApi";

/**
 * Ant Design Theme System
 */
export {
  createDefaultAntTheme,
  darkAntTheme,
  defaultAntTheme,
} from "./ant-theme";
// Use antd/lib (CJS) rather than antd (ESM) to prevent dual module instances
// that break ConfigProvider context and cause useToken() to return default tokens.
export { theme as antTheme } from "antd/lib";

/**
 * Custom ChakraUI Components (deprecated)
 * These components are custom to FidesUI and are not included in ChakraUI, although they may rely on ChakraUI components.
 */
export { CheckboxTree } from "./components/chakra-base/checkbox-tree";
export { ConfirmationModal } from "./components/chakra-base/confirmation-modal";
export { ExampleComponent } from "./components/chakra-base/example-component";
export { PrimaryLink, SecondaryLink } from "./components/chakra-base/links";
export { SystemsCheckboxTable } from "./components/chakra-base/systems-checkbox-table";

/**
 * Custom Hooks
 */
export type {
  ThemeMode,
  ThemeModeProviderProps,
  UseFormModalOptions,
} from "./hooks";
export { ThemeModeProvider, useFormModal, useThemeMode } from "./hooks";
