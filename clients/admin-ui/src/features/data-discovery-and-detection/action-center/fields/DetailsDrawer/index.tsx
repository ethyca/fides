import { AntDrawer as Drawer } from "fidesui";

import { DetailsDrawerFooter } from "./DetailsDrawerFooter";
import { DetailsDrawerTitle } from "./DetailsDrawerTitle";
import type { DetailsDrawerProps } from "./types";

export const DetailsDrawer = ({
  title,
  titleIcon,
  titleTag,
  actions,
  width = 480 /* TODO: add refactor for making this the default width for all drawers */,
  ...drawerProps
}: DetailsDrawerProps) => {
  return (
    <Drawer
      title={
        <DetailsDrawerTitle
          title={title}
          titleIcon={titleIcon}
          titleTag={titleTag}
        />
      }
      footer={
        drawerProps.footer || !actions ? (
          drawerProps.footer
        ) : (
          <DetailsDrawerFooter
            itemKey={drawerProps.itemKey}
            actions={actions}
          />
        )
      }
      width={width}
      {...drawerProps}
    />
  );
};
