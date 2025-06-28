<template>
  <div class="bool-field">
    <input 
      :id="fieldId" 
      type="checkbox" 
      :checked="modelValue === true" 
      :indeterminate="modelValue === null" 
      @change="handleChange"
      ref="checkboxRef"
    />
    <span class="bool-label">{{ labelText }}</span>
  </div>
</template>

<script setup>
import { computed, nextTick, watch, ref } from 'vue'

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: Boolean,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`
const checkboxRef = ref(null)

const labelText = computed(() => {
  if (props.modelValue === null) return 'Не вказано'
  return props.modelValue ? 'Так' : 'Ні'
})

function handleChange(event) {
  const value = event.target.indeterminate ? null : event.target.checked
  emit('update:modelValue', value)
}

// Set indeterminate state when value changes
watch(() => props.modelValue, async () => {
  await nextTick()
  if (checkboxRef.value) {
    checkboxRef.value.indeterminate = props.modelValue === null
  }
}, { immediate: true })
</script>

<style scoped>
.bool-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bool-label {
  font-size: 0.95em;
  color: #666;
}
</style> 