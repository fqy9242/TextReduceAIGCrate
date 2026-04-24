import { apiClient } from "@/api/client";
import type { PromptMeta } from "@/types";

export async function listPromptMetadata(): Promise<PromptMeta[]> {
  const { data } = await apiClient.get<{ items: PromptMeta[] }>("/prompts/metadata");
  return data.items;
}

export async function reloadPrompts(): Promise<void> {
  await apiClient.post("/prompts/reload");
}
