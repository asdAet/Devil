import { lazy, Suspense } from "react";

import type { CustomEmojiPickerProps } from "./CustomEmojiPicker";

const CustomEmojiPickerChunk = lazy(() =>
  import("./CustomEmojiPicker").then((module) => ({
    default: module.CustomEmojiPicker,
  })),
);

export function LazyCustomEmojiPicker(props: CustomEmojiPickerProps) {
  return (
    <Suspense fallback={null}>
      <CustomEmojiPickerChunk {...props} />
    </Suspense>
  );
}
