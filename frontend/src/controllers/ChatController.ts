import { apiService } from "../adapters/ApiService";
import type {
  EditMessageResult,
  GlobalSearchResult,
  ReactionResult,
  ReadStateResult,
  RoomAttachmentsResult,
  SearchResult,
  UnreadCountItem,
  UploadAttachmentsOptions,
  UploadResult,
} from "../domain/interfaces/IApiService";
import type {
  DirectChatsResponseDto,
  DirectStartResponseDto,
  RoomMessagesDto,
  RoomMessagesParams,
} from "../dto";
import type { RoomDetails as RoomDetailsDto } from "../entities/room/types";

let publicRoomInFlight: Promise<RoomDetailsDto> | null = null;
let directChatsInFlight: Promise<DirectChatsResponseDto> | null = null;

const roomDetailsInFlight = new Map<string, Promise<RoomDetailsDto>>();
const roomMessagesInFlight = new Map<string, Promise<RoomMessagesDto>>();

/**
 * ��������� ������� `buildRoomMessagesKey`.
 * @param roomId ������� �������� `roomId`.
 * @returns ��������� ���������� `buildRoomMessagesKey`.
 */

const buildRoomMessagesKey = (roomId: string, params?: RoomMessagesParams) => {
  const limit = params?.limit ?? "";
  const beforeId = params?.beforeId ?? "";
  return `${roomId}|limit=${limit}|before=${beforeId}`;
};

/**
 * ��������� ���������� ������ `ChatController`.
 */

class ChatController {
  /**
   * ��������� ����� `getPublicRoom`.
   * @returns ��������� ���������� `getPublicRoom`.
   */

  public async getPublicRoom(): Promise<RoomDetailsDto> {
    if (publicRoomInFlight) {
      return publicRoomInFlight;
    }

    publicRoomInFlight = apiService.getPublicRoom().finally(() => {
      publicRoomInFlight = null;
    });

    return publicRoomInFlight;
  }

  /**
   * ��������� ����� `getRoomDetails`.
   * @param roomId ������� �������� `roomId`.
   * @returns ��������� ���������� `getRoomDetails`.
   */

  public async getRoomDetails(roomId: string): Promise<RoomDetailsDto> {
    const inFlight = roomDetailsInFlight.get(roomId);
    if (inFlight) {
      return inFlight;
    }

    const request = apiService.getRoomDetails(roomId).finally(() => {
      roomDetailsInFlight.delete(roomId);
    });

    roomDetailsInFlight.set(roomId, request);
    return request;
  }

  /**
   * ��������� ����� `getRoomMessages`.
   * @param roomId ������� �������� `roomId`.
   * @returns ��������� ���������� `getRoomMessages`.
   */

  public async getRoomMessages(
    roomId: string,
    params?: RoomMessagesParams,
  ): Promise<RoomMessagesDto> {
    const cacheKey = buildRoomMessagesKey(roomId, params);
    const inFlight = roomMessagesInFlight.get(cacheKey);
    if (inFlight) {
      return inFlight;
    }

    const request = apiService.getRoomMessages(roomId, params).finally(() => {
      roomMessagesInFlight.delete(cacheKey);
    });

    roomMessagesInFlight.set(cacheKey, request);
    return request;
  }

  /**
   * ��������� ����� `startDirectChat`.
   * @param publicRef ������� �������� `publicRef`.
   * @returns ��������� ���������� `startDirectChat`.
   */

  public async startDirectChat(
    publicRef: string,
  ): Promise<DirectStartResponseDto> {
    const response = await apiService.startDirectChat(publicRef);
    return response;
  }

  /**
   * ��������� ����� `getDirectChats`.
   * @returns ��������� ���������� `getDirectChats`.
   */

  public async getDirectChats(): Promise<DirectChatsResponseDto> {
    if (directChatsInFlight) {
      return directChatsInFlight;
    }

    directChatsInFlight = apiService.getDirectChats().finally(() => {
      directChatsInFlight = null;
    });

    return directChatsInFlight;
  }
  public async getUnreadCounts(): Promise<UnreadCountItem[]> {
    return apiService.getUnreadCounts();
  }

  public async editMessage(
    roomId: string,
    messageId: number,
    content: string,
  ): Promise<EditMessageResult> {
    return apiService.editMessage(roomId, messageId, content);
  }

  public async deleteMessage(roomId: string, messageId: number): Promise<void> {
    return apiService.deleteMessage(roomId, messageId);
  }

  public async addReaction(
    roomId: string,
    messageId: number,
    emoji: string,
  ): Promise<ReactionResult> {
    return apiService.addReaction(roomId, messageId, emoji);
  }

  public async removeReaction(
    roomId: string,
    messageId: number,
    emoji: string,
  ): Promise<void> {
    return apiService.removeReaction(roomId, messageId, emoji);
  }

  public async searchMessages(
    roomId: string,
    query: string,
  ): Promise<SearchResult> {
    return apiService.searchMessages(roomId, query);
  }

  public async uploadAttachments(
    roomId: string,
    files: File[],
    options?: UploadAttachmentsOptions,
  ): Promise<UploadResult> {
    return apiService.uploadAttachments(roomId, files, options);
  }

  public async markRead(
    roomId: string,
    messageId?: number,
  ): Promise<ReadStateResult> {
    return apiService.markRead(roomId, messageId);
  }

  public async globalSearch(
    query: string,
    params?: {
      usersLimit?: number;
      groupsLimit?: number;
      messagesLimit?: number;
    },
  ): Promise<GlobalSearchResult> {
    return apiService.globalSearch(query, params);
  }

  public async getRoomAttachments(
    roomId: string,
    params?: { limit?: number; before?: number },
  ): Promise<RoomAttachmentsResult> {
    return apiService.getRoomAttachments(roomId, params);
  }
}

export const chatController = new ChatController();
