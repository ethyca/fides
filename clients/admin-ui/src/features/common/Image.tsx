// components/Image.js
import NextImage, { ImageProps } from "next/image";

// opt-out of image optimization, no-op
const customLoader = ({ src }: { src: string }) => src;

const Image = (props: ImageProps) => (
  <NextImage {...props} loader={customLoader} unoptimized />
);

export default Image;
