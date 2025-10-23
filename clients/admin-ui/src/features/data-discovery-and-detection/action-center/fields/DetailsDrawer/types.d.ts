import {
  AntDrawerProps as DrawerProps,
  AntTagProps as TagProps,
} from "fidesui";
import { ReactNode } from "react";

export type DetailsAction = {
  label: string;
  callback: (itemKey: string) => void;
};

export type DetailsDrawerProps = DrawerProps & {
  itemKey: string;
  titleIcon?: ReactNode;
  titleTag?: TagProps;
  actions?: DetailsAction[];
};
