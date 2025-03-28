<template>
  <div class="chat-setting-page">
    <arco-card title="聊天设置" :bordered="false">
      <arco-form 
        :model="formData" 
        layout="horizontal" 
        :label-col-props="{ span: 6 }" 
        :wrapper-col-props="{ span: 18 }"
        :label-align="'left'"
      >
        <arco-form-item field="modelProvider" label="模型提供方：">
          <arco-select v-model="formData.modelProvider" placeholder="请选择模型提供方">
            <arco-option value="openAI">openAI</arco-option>
            <arco-option value="azure">Azure</arco-option>
            <arco-option value="anthropic">Anthropic</arco-option>
          </arco-select>
        </arco-form-item>
        
        <arco-form-item field="apiKey" label="API密钥：">
          <arco-input-password v-model="formData.apiKey" placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxx" allow-clear />
        </arco-form-item>
        
        <arco-form-item field="apiAddress" label="API路径：">
          <arco-input v-model="formData.apiAddress" placeholder="请输入API路径" />
        </arco-form-item>
        
        <arco-form-item field="modelName" label="模型名称：">
          <arco-select v-model="formData.modelName" placeholder="请选择模型名称">
            <arco-option value="gpt-3.5-turbo">gpt-3.5-turbo</arco-option>
            <arco-option value="gpt-4">gpt-4</arco-option>
            <arco-option value="claude-3">claude-3</arco-option>
          </arco-select>
        </arco-form-item>
        
        <arco-form-item field="totalTokens" label="总Token数量：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.totalTokens" :min="1" :max="8" />
            <arco-input-number v-model="formData.totalTokens" :min="1" :max="8" />
            <!-- <span>K</span> -->
          </div>
        </arco-form-item>
        
        <arco-form-item field="outputTokens" label="输出Token数量：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.outputTokens" :min="128" :max="2048" :step="128" />
            <arco-input-number v-model="formData.outputTokens" :min="128" :max="2048" :step="128" />
          </div>
        </arco-form-item>
        
        <arco-form-item field="temperature" label="随机性：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.temperature" :min="0" :max="1" :step="0.01" />
            <arco-input-number v-model="formData.temperature" :min="0" :max="1" :step="0.01" :precision="2" />
          </div>
        </arco-form-item>
        
        <arco-form-item field="topP" label="累积概率阈值：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.topP" :min="0" :max="1" :step="0.01" />
            <arco-input-number v-model="formData.topP" :min="0" :max="1" :step="0.01" :precision="2" />
          </div>
        </arco-form-item>
        
        <arco-form-item field="retrievalLimit" label="检索数量上限：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.retrievalLimit" :min="1" :max="20" :step="1" />
            <arco-input-number v-model="formData.retrievalLimit" :min="1" :max="20" :step="1" />
          </div>
        </arco-form-item>
        
        <arco-form-item field="contextMessageCount" label="上下文消息数量：">
          <div class="token-input-wrapper">
            <arco-slider v-model="formData.contextMessageCount" :min="1" :max="50" :step="1" />
            <arco-input-number v-model="formData.contextMessageCount" :min="1" :max="50" :step="1" />
          </div>
        </arco-form-item>
        
        <arco-form-item>
          <arco-space>
            <arco-button type="primary" @click="saveSettings">保存设置</arco-button>
            <arco-button @click="resetSettings">重置</arco-button>
          </arco-space>
        </arco-form-item>
      </arco-form>
    </arco-card>
  </div>
  <!-- <ChatSettingForm /> -->
</template>

<script setup>
import { ref, reactive } from 'vue';
import { Message } from '@arco-design/web-vue';
import ChatSettingForm from '@/components/ChatSettingForm.vue';

const formData = reactive({
  modelProvider: 'openAI',
  apiKey: '',
  apiAddress: '',
  modelName: '',
  totalTokens: 4,
  outputTokens: 512,
  temperature: 0.50,
  topP: 1.00,
  retrievalLimit: 5,
  contextMessageCount: 10
});

const saveSettings = () => {
  // 保存设置的逻辑
  Message.success('设置已保存');
};

const resetSettings = () => {
  // 重置设置的逻辑
  Object.assign(formData, {
    modelProvider: 'openAI',
    apiKey: '',
    apiAddress: '',
    modelName: '',
    totalTokens: 4,
    outputTokens: 512,
    temperature: 0.50,
    topP: 1.00,
    retrievalLimit: 5,
    contextMessageCount: 10
  });
  Message.info('设置已重置');
};
</script>

<style scoped>
.chat-setting-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.token-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.token-input-wrapper .arco-slider {
  flex: 1;
  min-width: 200px;
  width: 100%;
}

.token-input-wrapper .arco-input-number {
  width: 100px;
  flex-shrink: 0;
}
</style>
