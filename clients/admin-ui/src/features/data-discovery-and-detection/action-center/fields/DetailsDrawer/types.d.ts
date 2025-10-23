import { AntDrawerProps as DrawerProps } from "fidesui";

export type DetailsAction = {
  label: string;
  callback: (itemKey: React.Key) => void;
};

export type DetailsDrawerProps = DrawerProps & {
  itemKey: React.Key;
  titleIcon?: ReactNode;
  titleTag?: TagProps;
  actions?: Record<string, DetailsAction>;
};
