<template>
  <div class="number-field">
    <input 
      :id="fieldId" 
      type="number" 
      class="pure-input-1" 
      :value="modelValue ?? ''" 
      @blur="handleBlur"
      :placeholder="field.placeholder"
      :min="field.min"
      :max="field.max"
      :step="field.step"
    />
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
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`

function handleBlur(event) {
  const newValue = event.target.value
  if (newValue !== (props.modelValue ?? '')) {
    emit('update:modelValue', newValue)
  }
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