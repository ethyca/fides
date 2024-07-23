import { YAMLException } from "js-yaml";
import { narrow } from "narrow-minded";
import dynamic from "next/dynamic";

export const Editor = dynamic(
  // @ts-ignore
  () => import("@monaco-editor/react").then((mod) => mod.default),
  { ssr: false },
);

export const isYamlException = (error: unknown): error is YAMLException =>
  narrow({ name: "string" }, error) && error.name === "YAMLException";
