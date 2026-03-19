import type { Attachment } from "../../../entities/message/types";
import {
  isImageAttachment,
  resolveImagePreviewUrl,
} from "../../../shared/lib/attachmentMedia";

export type AttachmentRenderItem = {
  attachment: Attachment;
  isImage: boolean;
  imageSrc: string | null;
};

export type ImageAttachmentRenderItem = {
  attachment: Attachment;
  imageSrc: string;
};

export type AttachmentBuckets = {
  images: ImageAttachmentRenderItem[];
  visibleImages: ImageAttachmentRenderItem[];
  hiddenImageCount: number;
  others: AttachmentRenderItem[];
};

export type MediaGridVariant = "single" | "two" | "three" | "four" | "many";

const normalizeVisibleImageLimit = (value: number): number => {
  if (!Number.isFinite(value)) return 1;
  return Math.max(1, Math.floor(value));
};

export const buildAttachmentRenderItems = (
  attachments: Attachment[],
): AttachmentRenderItem[] =>
  attachments.map((attachment) => {
    const imageSrc = resolveImagePreviewUrl({
      url: attachment.url,
      thumbnailUrl: attachment.thumbnailUrl,
      contentType: attachment.contentType,
      fileName: attachment.originalFilename,
    });

    return {
      attachment,
      isImage: isImageAttachment(
        attachment.contentType,
        attachment.originalFilename,
      ),
      imageSrc,
    };
  });

export const splitAttachmentRenderItems = (
  items: AttachmentRenderItem[],
  maxVisibleImages: number,
): AttachmentBuckets => {
  const images: ImageAttachmentRenderItem[] = [];
  const others: AttachmentRenderItem[] = [];

  for (const item of items) {
    if (item.isImage && item.imageSrc) {
      images.push({
        attachment: item.attachment,
        imageSrc: item.imageSrc,
      });
      continue;
    }
    others.push(item);
  }

  const visibleImages = images.slice(
    0,
    normalizeVisibleImageLimit(maxVisibleImages),
  );

  return {
    images,
    visibleImages,
    hiddenImageCount: images.length - visibleImages.length,
    others,
  };
};

export const resolveMediaGridVariant = (count: number): MediaGridVariant => {
  if (count <= 1) return "single";
  if (count === 2) return "two";
  if (count === 3) return "three";
  if (count === 4) return "four";
  return "many";
};

export const resolveImageAspectRatio = (attachment: Attachment): number => {
  if (
    attachment.width &&
    attachment.height &&
    attachment.width > 0 &&
    attachment.height > 0
  ) {
    const ratio = attachment.width / attachment.height;
    return Math.min(1.8, Math.max(0.62, ratio));
  }
  return 1;
};
