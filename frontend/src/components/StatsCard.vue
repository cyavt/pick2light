<template>
  <div class="stats-card card" :class="[`stats-${variant}`]">
    <div class="stats-body">
      <div class="stats-text">
        <div class="stats-label">{{ label }}</div>
        <div class="stats-value">{{ formattedValue }}</div>
      </div>
      <div class="stats-visual">
        <div class="stats-icon-wrap" :class="[`icon-${variant}`]">
          <span><i :class="icon"></i></span>
        </div>
      </div>
    </div>
    <div v-if="trend !== null" class="stats-footer">
      <span class="stats-trend" :class="{ up: trend > 0, down: trend < 0 }">
        {{ trend > 0 ? '↑' : '↓' }} {{ Math.abs(trend) }}%
      </span>
      <span class="trend-text">so với hôm qua</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, default: 'fa fa-th-large' },
  label: { type: String, required: true },
  value: { type: Number, required: true },
  variant: { type: String, default: 'default' },
  trend: { type: Number, default: null },
})

const formattedValue = computed(() => {
  if (props.value >= 1000) return props.value.toLocaleString()
  return props.value
})
</script>

<style scoped>
/* Inspinia ibox / widget style */
.stats-card {
  position: relative;
  overflow: hidden;
}

.stats-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats-label {
  font-size: 0.85em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
  letter-spacing: 0.02em;
}

.stats-value {
  font-size: 1.9rem;
  font-weight: 700;
  color: var(--text-heading);
  line-height: 1;
}

.stats-icon-wrap {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 1.4rem;
}
.icon-default { background: rgba(26, 179, 148, 0.12); color: var(--primary); }
.icon-success { background: rgba(28, 132, 198, 0.12); color: var(--success); }
.icon-warning { background: rgba(248, 172, 89, 0.12); color: var(--warning); }
.icon-danger { background: rgba(237, 85, 101, 0.12); color: var(--danger); }

.stats-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  font-size: 0.85em;
}
.stats-trend {
  font-weight: 700;
}
.stats-trend.up { color: var(--primary); }
.stats-trend.down { color: var(--danger); }

.trend-text {
  color: var(--text-muted);
}
</style>
