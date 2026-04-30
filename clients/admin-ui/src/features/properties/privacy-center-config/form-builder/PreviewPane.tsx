import { JSONUIProvider, Renderer } from "@json-render/react";
import { Empty } from "fidesui";
import React from "react";

import type { JsonRenderSpec } from "./mapper";
import { registry } from "./registry";

interface PreviewPaneProps {
  spec: JsonRenderSpec | null;
  onFieldClick: (elementId: string) => void;
}

// Privacy-center-inspired canvas: light grey backdrop, white card with
// subtle shadow, narrow column to mirror the actual rendered form width.
const canvasStyle: React.CSSProperties = {
  background: "#f5f5f5",
  width: "100%",
  height: "100%",
  minHeight: 480,
  padding: 32,
  display: "flex",
  justifyContent: "center",
  alignItems: "flex-start",
  overflowY: "auto",
};

const formCardStyle: React.CSSProperties = {
  background: "white",
  width: "100%",
  maxWidth: 360,
  padding: 32,
  borderRadius: 4,
  boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
};

export const PreviewPane = ({ spec, onFieldClick }: PreviewPaneProps) => {
  if (!spec) {
    return (
      <div style={canvasStyle}>
        <div style={formCardStyle}>
          <Empty description="Start by chatting with the form builder." />
        </div>
      </div>
    );
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
        const { visible, watch, ...rest } =
          element as JsonRenderSpec["elements"][string] & {
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

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
    <div style={canvasStyle} onClick={handleClick}>
      <div style={formCardStyle}>
        <JSONUIProvider registry={registry}>
          <Renderer spec={wrappedSpec as any} registry={registry} />
        </JSONUIProvider>
      </div>
    </div>
  );
};
