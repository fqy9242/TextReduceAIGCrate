import { computed, ref } from "vue";
import { defineStore } from "pinia";
import * as authApi from "@/api/auth";
import { tokenStore } from "@/api/client";

const USERNAME_KEY = "aigc_username";

export const useAuthStore = defineStore("auth", () => {
  const username = ref(localStorage.getItem(USERNAME_KEY) ?? "");

  const isAuthenticated = computed(() => Boolean(tokenStore.getAccessToken()));

  async function login(usernameInput: string, password: string): Promise<void> {
    const tokens = await authApi.login(usernameInput, password);
    tokenStore.setTokens(tokens);
    username.value = usernameInput;
    localStorage.setItem(USERNAME_KEY, usernameInput);
  }

  async function logout(): Promise<void> {
    try {
      if (tokenStore.getAccessToken()) {
        await authApi.logout();
      }
    } finally {
      tokenStore.clear();
      username.value = "";
      localStorage.removeItem(USERNAME_KEY);
    }
  }

  return {
    username,
    isAuthenticated,
    login,
    logout,
  };
});
