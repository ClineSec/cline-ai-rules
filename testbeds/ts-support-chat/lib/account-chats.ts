import type { UIMessage } from "ai";
import { prisma } from "./db";

/** The stored conversation for an account-assistant chat, oldest first. */
export async function loadAccountChat(chatId: string): Promise<UIMessage[]> {
  const rows = await prisma.accountChatMessage.findMany({
    where: { chatId },
    orderBy: { createdAt: "asc" },
  });
  return rows.map((row) => row.message as unknown as UIMessage);
}

export async function saveAccountChat(chatId: string, messages: UIMessage[]) {
  await prisma.$transaction([
    prisma.accountChatMessage.deleteMany({ where: { chatId } }),
    prisma.accountChatMessage.createMany({
      data: messages.map((message, i) => ({ chatId, position: i, message: message as object })),
    }),
  ]);
}
