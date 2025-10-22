import { AntDrawerProps as DrawerProps } from "fidesui";

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
