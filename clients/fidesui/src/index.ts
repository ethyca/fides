// Unmodified components exported directly from ChakraUI
export * from "@chakra-ui/icons";
export * from "@chakra-ui/react";
export { getCSSVar } from "@chakra-ui/utils";
export * from "@chakra-ui/utils";

// Unmodified component exported directly from Ant Design
export type { ThemeConfig as AntThemeConfig } from "antd/es";
export type { SwitchProps as AntSwitchProps } from "antd/lib";
export type { ButtonProps as AntButtonProps } from "antd/lib";
export { Layout as AntLayout } from "antd/lib";
export { Space as AntSpace } from "antd/lib";
export { Col as AntCol, Row as AntRow } from "antd/lib";
export { Typography as AntTypography } from "antd/lib";
export { Card as AntCard } from "antd/lib";
export { Button as AntButton } from "antd/lib";
export { Form as AntForm } from "antd/lib";
export { Switch as AntSwitch } from "antd/lib";
export { Select as AntSelect } from "antd/lib";
export { Tooltip as AntTooltip } from "antd/lib";
export { Alert as AntAlert } from "antd/lib";
export { Tag as AntTag } from "antd/lib";
export { Input as AntInput } from "antd/lib";

/**
 * Custom Re-exports
 *
 * Icons whose names conflict with Chakra's included icons must be explicitly listed. This makes
 * typescript happy, but eslint doesn't understand.
 */
/* eslint-disable import/export */
export { AddIcon, LinkIcon, QuestionIcon, WarningIcon } from "./icons";
export * from "./icons";
/* eslint-enable import/export */

export * from "./FidesUIProvider";
export { extendTheme, theme } from "./FidesUITheme";

/**
 * Custom Components
 * These components are custom to FidesUI and are not included in ChakraUI, although they may rely on ChakraUI components.
 */
export { CheckboxTree } from "./components/checkbox-tree";
export { ClassifiedDataCategoryDropdown } from "./components/classified-data-category-dropdown";
export type { ColumnMetadata } from "./components/column-dropdown";
export { ColumnDropdown } from "./components/column-dropdown";
export { ConfirmationModal } from "./components/confirmation-modal";
export { DataCategoryDropdown } from "./components/data-category-dropdown";
export { ExampleComponent } from "./components/example-component";
export { PrimaryLink, SecondaryLink } from "./components/links";
export { SystemsCheckboxTable } from "./components/systems-checkbox-table";
