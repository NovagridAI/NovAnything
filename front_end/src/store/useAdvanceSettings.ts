import { defineStore } from 'pinia';

export const useAdvanceSettings = defineStore('advanceSettings', {
  state: () => ({
    modelType: '',
    apiContextLength: 4096,
    maxToken: 1024,
    temperature: 0.7,
    top_P: 1.0,
    top_K: 40,
    context: 5,
  }),

  actions: {
    updateSettings(settings: Partial<typeof this.$state>) {
      Object.assign(this.$state, settings);
    },
  },
}); 