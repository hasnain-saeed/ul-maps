export interface IconOptions {
  size?: number;
  backgroundColor?: string;
  textColor?: string;
  font?: string;
}

export const createCircularTextIcon = (
  text: string,
  options: IconOptions = {}
): ImageData => {
  const {
    size = 32,
    backgroundColor = '#dfa32a',
    textColor = '#ffffff',
    font = `bold ${size * 0.5}px Arial`,
  } = options;

  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = backgroundColor;
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2, 0, 2 * Math.PI);
  ctx.fill();

  ctx.fillStyle = textColor;
  ctx.font = font;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, size / 2, size / 2 + 1); // +1 for better vertical centering

  return ctx.getImageData(0, 0, size, size);
};