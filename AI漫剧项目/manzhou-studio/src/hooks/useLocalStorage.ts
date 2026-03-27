import { useCallback, useRef } from 'react';

interface StorageOptions<T> {
  deserialize?: (raw: string) => T;
  serialize?: (value: T) => string;
  key: string;
}

export function useLocalStorage<T>({
  key,
  deserialize = JSON.parse,
  serialize = JSON.stringify,
}: StorageOptions<T>) {
  const storedValue = (() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (deserialize(raw) as T) : null;
    } catch {
      return null;
    }
  })();

  const setItem = useCallback(
    (value: T | null | ((prev: T | null) => T)) => {
      try {
        if (value === null) {
          localStorage.removeItem(key);
        } else {
          const next = typeof value === 'function'
            ? (value as (prev: T | null) => T)(storedValue)
            : value;
          localStorage.setItem(key, serialize(next));
        }
      } catch (e) {
        console.warn(`[useLocalStorage] Failed to persist "${key}":`, e);
      }
    },
    [key, serialize],
  );

  return [storedValue, setItem] as const;
}

// 通用 useRef 避免闭包陈旧值
export function useLatest<T>(value: T) {
  const ref = useRef(value);
  ref.current = value;
  return ref;
}
