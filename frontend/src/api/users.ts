import { apiClient } from "@/api/client";
import type { UserOut } from "@/types";

export async function listUsers(): Promise<UserOut[]> {
  const { data } = await apiClient.get<UserOut[]>("/users");
  return data;
}

export async function createUser(username: string, password: string, role: string): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>("/users", {
    username,
    password,
    role,
  });
  return data;
}

export async function updateUserRole(userId: number, role: string): Promise<UserOut> {
  const { data } = await apiClient.patch<UserOut>(`/users/${userId}/role`, { role });
  return data;
}
