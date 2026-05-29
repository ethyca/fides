import { capitalize } from "lodash";
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";

import { ClassificationBreakdownItem } from "~/types/api/models/ClassificationBreakdownItem";

export const getRootClassifications = (
  classifications: Array<ClassificationBreakdownItem>,
) => {
  const reducedObj = classifications.reduce(
    (agg, current) => {
      const rootName = current.data_use.split(".")[0];

      const newEntry = {
        ...current,
        data_use: rootName,
        name: capitalize(rootName.replaceAll("_", " ")),
        vendors: [
          ...(agg?.[rootName]?.vendors ?? []),
          ...(current.vendors ?? []),
        ],
      };

      return { ...agg, [rootName]: newEntry };
    },
    {} as Record<string, ClassificationBreakdownItem>,
  );
  return Object.values(reducedObj);
};

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = filename || "download";

  const clickHandler = () => {
    setTimeout(() => {
      URL.revokeObjectURL(url);
      a.removeEventListener("click", clickHandler);
    }, 150);
  };

  a.addEventListener("click", clickHandler, false);

  a.click();
}

export const createImgSrc = (svgNode: SVGSVGElement | null) =>
  new Promise<string | null>((resolve) => {
    if (svgNode === null) {
      resolve(null);
      return;
    }

    const svgString = new XMLSerializer().serializeToString(svgNode);
    const canvas = document.createElement("canvas");
    canvas.height = 1200;
    canvas.width = 1200;

    const ctx = canvas.getContext("2d");
    const img = document.createElement("img");
    const base64 = Buffer.from(svgString, "utf-8").toString("base64");
    const imgSource = `data:image/svg+xml;base64,${base64}`;

    img.setAttribute("src", imgSource);
    img.onload = () => {
      ctx?.drawImage(img, 0, 0);
      const pngData = canvas.toDataURL("image/png");

      resolve(pngData);
    };
  });

export const generateChart = async (Chart: React.ReactNode) => {
  const div = document.createElement("div");
  const root = createRoot(div);

  flushSync(() => {
    root.render(Chart);
  });

  const svgNode = div.childNodes[0]?.childNodes[0];
  const vendorChart = await createImgSrc(svgNode as SVGSVGElement);

  return vendorChart;
};

export const getImageBlob = async (imageSrc: string) =>
  fetch(imageSrc, {
    method: "GET",
  })
    .then((response) => response.blob())
    .then((blob) => {
      const source = URL.createObjectURL(blob);
      return source;
    })
    .catch(() => {
      return "";
    });
