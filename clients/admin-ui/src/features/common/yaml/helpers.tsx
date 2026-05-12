import { YAMLException } from "js-yaml";
import { narrow } from "narrow-minded";
import dynamic from "next/dynamic";
import React from "react";

import ClipboardButton from "~/features/common/ClipboardButton";

export const Editor = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.default),
  { ssr: false },
);

export const EditorWithCopy = ({ yaml }: { yaml: string }) => (
  <div className="relative">
    <Editor
      defaultLanguage="yaml"
      value={yaml}
      height="60vh"
      options={{
        readOnly: true,
        minimap: { enabled: false },
        fontSize: 13,
        fontFamily: "Menlo",
        scrollBeyondLastLine: false,
      }}
      theme="light"
    />
    <div className="absolute right-2 top-2 z-10">
      <ClipboardButton copyText={yaml} size="small" />
    </div>
  </div>
);

export const isYamlException = (error: unknown): error is YAMLException =>
  narrow({ name: "string" }, error) && error.name === "YAMLException";
