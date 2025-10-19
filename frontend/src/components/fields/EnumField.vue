<template>
  <div class="enum-field">
    <select :id="fieldId" class="pure-input-1" :value="modelValue ?? ''" @change="handleChange">
      <option :value="''">—</option>
      <option v-for="option in field.values" :key="option" :value="option">{{ option }}</option>
    </select>
    <div v-if="field.description" class="field-description">
      {{ field.description }}
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`

function handleChange(event) {
  const value = event.target.value === '' ? null : event.target.value
  emit('update:modelValue', value)
}
</script>

<style scoped>
.field-description {
  font-size: 0.85em;
  color: #666;
  margin-top: 0.25rem;
  line-height: 1.3;
}
</style> 