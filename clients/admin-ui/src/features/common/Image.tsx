// components/Image.js
import NextImage from 'next/image';

// opt-out of image optimization, no-op
const customLoader = ({ src }: { src: string }) => src;

const Image: typeof NextImage = (props) => (
  <NextImage {...props} loader={customLoader} unoptimized />
);

export default Image;
