import { apiClient } from "@/api/client";
import type { PromptDetail, PromptMeta } from "@/types";

export interface UpdatePromptPayload {
  version: string;
  variables: string[];
  system: string;
  human: string;
  instruction: string;
}

export async function listPromptMetadata(): Promise<PromptMeta[]> {
  const { data } = await apiClient.get<{ items: PromptMeta[] }>("/prompts/metadata");
  return data.items;
}

export async function reloadPrompts(): Promise<void> {
  await apiClient.post("/prompts/reload");
}

export async function getPromptDetail(group: string, name: string): Promise<PromptDetail> {
  const { data } = await apiClient.get<PromptDetail>(`/prompts/${group}/${name}`);
  return data;
}

export async function updatePrompt(group: string, name: string, payload: UpdatePromptPayload): Promise<void> {
  await apiClient.put(`/prompts/${group}/${name}`, payload);
}
