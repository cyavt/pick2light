/**
 * Theme composable — dark/light mode toggle (Inspinia style).
 * Light mode is the default (Inspinia standard).
 * Persists preference in localStorage.
 */

import { ref, watch } from 'vue'

const theme = ref('light')

export function useTheme() {
  function initTheme() {
    const saved = localStorage.getItem('ptl-theme')
    if (saved) {
      theme.value = saved
    } else {
      // Inspinia defaults to light; only use dark if OS explicitly prefers it
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
    applyTheme()
  }

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('ptl-theme', theme.value)
    applyTheme()
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  const isDark = ref(false)
  watch(theme, (val) => {
    isDark.value = val === 'dark'
  }, { immediate: true })

  return { theme, isDark, toggleTheme, initTheme }
}
