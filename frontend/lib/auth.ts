import { authApi, User } from './api';

export const TOKEN_KEY = 'token';
export const USER_KEY = 'user';

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem(USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr) as User;
      } catch {
        return null;
      }
    }
  }
  return null;
}

export async function fetchCurrentUser(): Promise<User | null> {
  try {
    const user = await authApi.getMe();
    setUser(user);
    return user;
  } catch {
    removeToken();
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

