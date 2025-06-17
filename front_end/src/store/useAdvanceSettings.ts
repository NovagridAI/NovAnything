import { defineStore } from 'pinia';
import { reactive } from 'vue';

interface AdvanceSettings {
  modelType: string;
  apiContextLength: number;
  maxToken: number;
  temperature: number;
  top_P: number;
  top_K: number;
  context: number;
}

export const useAdvanceSettings = defineStore('advanceSettings', () => {
  // state
  const userSettings = reactive<AdvanceSettings>({
    modelType: '',
    apiContextLength: 4096,
    maxToken: 1024,
    temperature: 0.7,
    top_P: 1.0,
    top_K: 40,
    context: 5,
  });

  // actions
  function updateSettings(newSettings: Partial<AdvanceSettings>) {
    console.log('newSettings', newSettings);
    Object.assign(userSettings, newSettings);
  }

  return {
    userSettings,
    updateSettings,
  };
}); 