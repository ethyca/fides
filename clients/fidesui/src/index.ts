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
  extendTheme as extendChakraTheme,
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

/**
 * @deprecated Chakra UI icons are deprecated and will be removed in a future release.
 * Please use Carbon icons (Icons.*) instead.
 */
export {
  ArrowBackIcon as ChakraArrowBackIcon,
  ArrowDownIcon as ChakraArrowDownIcon,
  ArrowForwardIcon as ChakraArrowForwardIcon,
  ArrowUpIcon as ChakraArrowUpIcon,
  BellIcon as ChakraBellIcon,
  CheckCircleIcon as ChakraCheckCircleIcon,
  CheckIcon as ChakraCheckIcon,
  ChevronDownIcon as ChakraChevronDownIcon,
  ChevronLeftIcon as ChakraChevronLeftIcon,
  ChevronRightIcon as ChakraChevronRightIcon,
  ChevronUpIcon as ChakraChevronUpIcon,
  CloseIcon as ChakraCloseIcon,
  DeleteIcon as ChakraDeleteIcon,
  DragHandleIcon as ChakraDragHandleIcon,
  EditIcon as ChakraEditIcon,
  ExternalLinkIcon as ChakraExternalLinkIcon,
  RepeatClockIcon as ChakraRepeatClockIcon,
  RepeatIcon as ChakraRepeatIcon,
  SmallAddIcon as ChakraSmallAddIcon,
  SmallCloseIcon as ChakraSmallCloseIcon,
  ViewOffIcon as ChakraViewOffIcon,
  WarningTwoIcon as ChakraWarningTwoIcon,
  // Icon utilities
  createIcon as createChakraIcon,
} from "@chakra-ui/icons";

// Unmodified component exported directly from Ant Design
export type { LocationSelectProps } from "./components/data-entry/LocationSelect";
export { LocationSelect } from "./components/data-entry/LocationSelect";
export type { ThemeConfig } from "antd/es";
export type {
  FilterValue,
  SorterResult,
  TablePaginationConfig,
} from "antd/es/table/interface";
export type {
  AvatarProps,
  ButtonProps,
  CheckboxProps,
  CollapseProps,
  DatePickerProps,
  DrawerProps,
  DropdownProps,
  FlexProps,
  FormInstance,
  FormItemProps,
  GetProps,
  InputProps as InputPropsOriginal,
  InputRef,
  MenuProps,
  ModalProps,
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
  Alert,
  AutoComplete,
  Avatar,
  Badge,
  Breadcrumb,
  Button,
  Card,
  Cascader,
  Checkbox,
  Col,
  Collapse,
  DatePicker,
  Descriptions,
  Divider,
  Drawer,
  Dropdown,
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
  Popover,
  Progress,
  Radio,
  Result,
  Row,
  Segmented,
  Skeleton,
  Space,
  Spin,
  Splitter,
  Steps,
  Switch,
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
export type { DisplayValueType } from "rc-select/lib/BaseSelect";

// Higher-order components
export type {
  ICustomMultiSelectProps,
  ICustomSelectProps,
  CustomInputProps as InputProps,
} from "./hoc";
export {
  CopyTooltip,
  CustomDateRangePicker as DateRangePicker,
  CustomInput as Input,
  CustomList as List,
  CustomSelect as Select,
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
export type { FilterProps } from "./components/data-display/Filter";
export { Filter } from "./components/data-display/Filter";

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

// Export the destructured Typography components individually
export const { Text, Title, Paragraph, Link } = CustomTypography;

/**
 * Custom Re-exports
 *
 * Icons whose names conflict with Chakra's included icons must be explicitly listed. This makes
 * typescript happy, but eslint doesn't understand.
 */
/* eslint-disable import/export */
export { AddIcon, LinkIcon, WarningIcon } from "./icons";
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
export * as Icons from "@carbon/icons-react";
/* end prefixed icons */

export { FidesUIProvider, useMessage, useModal } from "./FidesUIProvider";
export { extendTheme, theme } from "./FidesUITheme";

/**
 * Ant Design Theme System
 */
export { createDefaultAntTheme, defaultAntTheme } from "./ant-theme";
export { theme as antTheme } from "antd";

/**
 * Custom Components
 * These components are custom to FidesUI and are not included in ChakraUI, although they may rely on ChakraUI components.
 */
export { CheckboxTree } from "./components/chakra-base/checkbox-tree";
export type { ColumnMetadata } from "./components/chakra-base/column-dropdown";
export { ColumnDropdown } from "./components/chakra-base/column-dropdown";
export { ConfirmationModal } from "./components/chakra-base/confirmation-modal";
export { DataCategoryDropdown } from "./components/chakra-base/data-category-dropdown";
export { ExampleComponent } from "./components/chakra-base/example-component";
export { PrimaryLink, SecondaryLink } from "./components/chakra-base/links";
export { SystemsCheckboxTable } from "./components/chakra-base/systems-checkbox-table";
export { SelectInline } from "./components/data-entry/SelectInline";
export { FloatingMenu } from "./components/navigation";

/**
 * Custom Hooks
 */
export type { UseFormModalOptions } from "./hooks";
export { useFormModal } from "./hooks";
