/**
 * Offline Cache — AsyncStorage task cache.
 * SRS §7 NFR-05: tasks/barcodes viewable offline. Evidence upload requires internet.
 * Cache is refreshed on every successful foreground event (Law 1 — Pull on Focus).
 * No silent background sync — wait for user to be online.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEYS = {
  TASKS: 'lumine_cached_tasks',
  CACHE_TIMESTAMP: 'lumine_cache_timestamp',
} as const;

export interface CachedTask {
  id: number;
  customer_id: string;
  task_type: '2D' | '2W' | '2M';
  task_basis: string;
  due_date: string;
  calculated_from: string;
  status: 'Pending' | 'Done' | 'Superseded';
  staff_name: string | null;  // null for tasks uploaded before migration 0005
  customer_name: string | null;  // null for tasks uploaded before migration 0010 or absent from source file
  created_at: string;
  updated_at: string;
}

export const offlineCache = {
  /**
   * Save the latest task list from a successful API fetch.
   * Called after every Pull on Focus succeeds.
   */
  async saveTasks(tasks: CachedTask[]): Promise<void> {
    await Promise.all([
      AsyncStorage.setItem(CACHE_KEYS.TASKS, JSON.stringify(tasks)),
      AsyncStorage.setItem(CACHE_KEYS.CACHE_TIMESTAMP, new Date().toISOString()),
    ]);
  },

  /**
   * Return cached tasks (for offline display).
   * Returns empty array if cache is empty.
   */
  async getTasks(): Promise<CachedTask[]> {
    const raw = await AsyncStorage.getItem(CACHE_KEYS.TASKS);
    if (!raw) return [];
    try {
      return JSON.parse(raw) as CachedTask[];
    } catch {
      return [];
    }
  },

  async getCacheTimestamp(): Promise<string | null> {
    return AsyncStorage.getItem(CACHE_KEYS.CACHE_TIMESTAMP);
  },

  async clearCache(): Promise<void> {
    await Promise.all([
      AsyncStorage.removeItem(CACHE_KEYS.TASKS),
      AsyncStorage.removeItem(CACHE_KEYS.CACHE_TIMESTAMP),
    ]);
  },
};
