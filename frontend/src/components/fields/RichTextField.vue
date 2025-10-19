<template>
  <div class="rich-text-field">
    <textarea 
      :id="fieldId" 
      class="pure-input-1" 
      :value="modelValue ?? ''" 
      @blur="handleBlur"
      :placeholder="field.placeholder"
      rows="3"
    ></textarea>
    <div v-if="field.description" class="field-description">
      {{ $t(`fields.${field.key}.description`, field.description) }}
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