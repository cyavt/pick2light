<template>
  <div v-if="$route.name === 'Login'">
    <router-view />
  </div>
  <div v-else class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()
onMounted(() => initTheme())
</script>
