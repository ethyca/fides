import { JSONUIProvider, Renderer } from "@json-render/react";
import { Empty } from "fidesui";
import React from "react";

import type { JsonRenderSpec } from "./mapper";
import { registry } from "./registry";

interface PreviewPaneProps {
  spec: JsonRenderSpec | null;
  onFieldClick: (elementId: string) => void;
}

export const PreviewPane: React.FC<PreviewPaneProps> = ({
  spec,
  onFieldClick,
}) => {
  if (!spec) {
    return <Empty description="Start by chatting with the form builder." />;
  }

  const handleClick: React.MouseEventHandler<HTMLDivElement> = (event) => {
    const target = (event.target as HTMLElement).closest("[data-element-id]");
    if (target) {
      const id = target.getAttribute("data-element-id");
      if (id) {
        onFieldClick(id);
      }
    }
  };

  // Wrap each child element with data-element-id so click-to-edit can identify it.
  const wrappedSpec: JsonRenderSpec = {
    ...spec,
    elements: Object.fromEntries(
      Object.entries(spec.elements).map(([id, element]) => {
        // Strip preview-blocking conditional features so all fields render
        // unconditionally in the admin builder preview. The dropped-features
        // modal handles user communication at save time.
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { visible, watch, ...rest } = element as JsonRenderSpec["elements"][string] & {
          visible?: unknown;
          watch?: unknown;
        };
        return [
          id,
          {
            ...rest,
            props: {
              ...rest.props,
              "data-element-id": id,
            },
          },
        ];
      }),
    ),
  };

  // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
  return (
    <div onClick={handleClick}>
      <JSONUIProvider registry={registry}>
        <Renderer spec={wrappedSpec as any} registry={registry} />
      </JSONUIProvider>
    </div>
  );
};
