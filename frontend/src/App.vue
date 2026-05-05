<template>
  <!-- Wait for router to resolve before rendering anything -->
  <template v-if="routerReady">
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import { useTheme } from './composables/useTheme'

const router = useRouter()
const routerReady = ref(false)
const { initTheme } = useTheme()

onMounted(async () => {
  initTheme()
  await router.isReady()
  routerReady.value = true
})
</script>
