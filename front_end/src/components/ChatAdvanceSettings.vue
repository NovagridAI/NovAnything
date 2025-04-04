<template>
  <div class="settings-popover">
    <h3>高级参数</h3>

    <arco-form ref="formRef" :model="formData" layout="horizontal" :label-col-props="{ span: 6 }"
      :wrapper-col-props="{ span: 18 }" :label-align="'left'">
      <arco-form-item field="apiContextLength" label="总Token数量：">
        <template #label>
          <div class="label-with-tooltip">
            总Token数量：
            <arco-tooltip content="LLM输入和输出的总token数量上限">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="apiContextTokenK" :min="modelType === 'ollama' ? 2 : 4" :max="openAIModelMax || 200"
            :step="1" />
          <arco-input-number v-model="apiContextTokenK" :min="modelType === 'ollama' ? 2 : 4"
            :max="openAIModelMax || 200" :step="1" :precision="0" :hide-button="true">
            <template #append>K</template>
          </arco-input-number>
        </div>
      </arco-form-item>

      <arco-form-item field="maxToken" label="输出Token数量：">
        <template #label>
          <div class="label-with-tooltip">
            输出Token数量：
            <arco-tooltip content="LLM输出的token数量上限，最大值为: 总Token数量 / 4">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO" :step="1" />
          <arco-input-number v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO"
            :step="1" :precision="0" :hide-button="true" />
        </div>
      </arco-form-item>

      <arco-form-item field="temperature" label="随机性：">
        <template #label>
          <div class="label-with-tooltip">
            随机性：
            <arco-tooltip content="控制输出的随机性，较低值使输出更确定，较高值增加创意性">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="formData.temperature" :min="0" :max="1" :step="0.01" />
          <arco-input-number v-model="formData.temperature" :min="0" :max="1" :step="0.01" :precision="2"
            :hide-button="true" />
        </div>
      </arco-form-item>

      <arco-form-item field="top_P" label="累积概率阈值：">
        <template #label>
          <div class="label-with-tooltip">
            累积概率阈值：
            <arco-tooltip content="限制词汇选择范围，较低值使输出更聚焦，较高值增加多样性">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="formData.top_P" :min="0" :max="1" :step="0.01" />
          <arco-input-number v-model="formData.top_P" :min="0" :max="1" :step="0.01" :precision="2"
            :hide-button="true" />
        </div>
      </arco-form-item>

      <arco-form-item field="top_K" label="检索结果数量上限：">
        <template #label>
          <div class="label-with-tooltip">
            检索结果数量上限：
            <arco-tooltip content="检索算法取所有文档分片里最相关的分片数量上限">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="formData.top_K" :min="1" :max="100" :step="1" />
          <arco-input-number v-model="formData.top_K" :min="1" :max="100" :step="1" :precision="0"
            :hide-button="true" />
        </div>
      </arco-form-item>

      <arco-form-item field="context" label="上下文消息数量：">
        <template #label>
          <div class="label-with-tooltip">
            上下文消息数量：
            <arco-tooltip content="单轮对话中保留的历史消息数量上限">
              <icon-question-circle />
            </arco-tooltip>
          </div>
        </template>
        <div class="param-control">
          <arco-slider v-model="formData.context" :min="0" :max="11" :step="1" :format-tooltip="sliderFormatter" />
        </div>
      </arco-form-item>
    </arco-form>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { IconQuestionCircle } from '@arco-design/web-vue/es/icon';
import { useChatSetting } from '@/store/useChatSetting';
import { storeToRefs } from 'pinia';
import urlResquest from '@/services/urlConfig';
import { debounce } from 'lodash-es';

// 获取全局状态
const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { setAllChatSettingConfigured } = useChatSetting();

// 常量
const TOKENRATIO = 4;

// 表单引用
const formRef = ref(null);

// 模型类型
const modelType = ref('openAI');
const openAIModelMax = ref(200);

// 表单数据
const formData = reactive({
  modelType: '',
  modelName: '',
  apiKey: '',
  apiBase: '',
  apiModelName: '',
  apiContextLength: 4096,
  maxToken: 1024,
  temperature: 0.7,
  top_P: 1.0,
  top_K: 40,
  context: 10,
  capabilities: {}
});

// 上下文长度，单位k
const apiContextTokenK = ref(4);

// 添加一个标志来跟踪是否是首次加载
const isInitialLoad = ref(true);

// 上下文条数格式化
const sliderFormatter = (value) => {
  return value >= 11 ? '无限制' : value;
};

// 监听apiContextLength变化
watch(
  () => formData.apiContextLength,
  () => {
    apiContextTokenK.value = formData.apiContextLength / 1024;
  }
);

// 监听apiContextTokenK变化
watch(
  () => apiContextTokenK.value,
  () => {
    formData.apiContextLength = apiContextTokenK.value * 1024;
  }
);

// 添加模型列表状态
const modelList = ref([]);

// 获取模型列表
const fetchModelList = async () => {
  try {
    const response = await urlResquest.getModelList({}, {});
    if (response && response.data) {
      modelList.value = response.data.configs;
      console.log('获取到的模型列表:', modelList.value);

      // 将API返回的模型数据映射到chatSettingConfigured格式
      updateChatSettingWithModelList(modelList.value);
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models) => {
  if (!models || models.length === 0) return;

  // 将API返回的模型映射为chatSettingConfigured格式
  const customModels = models.map(model => {
    return {
      ...formData, // 使用基础表单数据作为模板
      modelType: model.model_endpoint,
      modelName: model.service_name,
      customId: model.config_id,
      apiKey: model.api_key,
      apiBase: model.api_proxy,
      chunkSize: model.chunk_size || 800,
      apiModelName: model.service_name,
      apiContextLength: model.token_limit || 4096,
      maxToken: Math.floor((model.token_limit || 4096) / TOKENRATIO),
      temperature: model.creativity || 0.5,
      top_P: model.vocabulary_richness || 1.0,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      },
      active: false,
      // 保存原始数据，以便后续可能需要
      originalData: { ...model }
    };
  });

  // 更新chatSettingConfigured，使用新的批量设置函数
  setAllChatSettingConfigured([...customModels]);
};

// 初始化表单
const initForm = () => {
  // 设置isInitialLoad为true，防止初始化触发更新
  isInitialLoad.value = true;

  const activeForm = { ...chatSettingConfigured.value.find(item => item.active === true) };
  Object.assign(formData, activeForm);

  // 设置模型类型
  modelType.value = activeForm.modelType || 'openAI';

  // 设置一个较长的延时，确保所有初始化操作完成后再将isInitialLoad设为false
  setTimeout(() => {
    console.log('初始化完成，允许更新');
    isInitialLoad.value = false;
  }, 1500);
};

// 在组件挂载时获取模型列表和初始化表单
onMounted(() => {
  // 确保isInitialLoad为true
  isInitialLoad.value = true;

  // 获取模型列表，然后初始化表单
  fetchModelList().then(() => {
    // 在获取模型列表成功后初始化表单
    initForm();

    // 设置一个延时，确保所有初始化操作完成后再将isInitialLoad设为false
    setTimeout(() => {
      console.log('组件挂载完成，允许更新');
      isInitialLoad.value = false;
    }, 1500);
  }).catch(error => {
    console.error('获取模型列表失败:', error);
    // 即使获取模型列表失败，也尝试初始化表单
    initForm();

    setTimeout(() => {
      isInitialLoad.value = false;
    }, 1500);
  });
});

// 监听chatSettingConfigured变化
watch(
  () => chatSettingConfigured.value,
  (newValue) => {
    // 如果不是首次加载，则更新表单数据
    console.log('chatSettingConfigured变化，更新表单数据');
    // 获取当前激活的模型配置
    const activeConfig = newValue.find(item => item.active === true);
    if (activeConfig) {
      // 更新表单数据
      Object.assign(formData, activeConfig);
      // 更新模型类型
      modelType.value = activeConfig.modelType || 'openAI';
      // 更新上下文长度
      apiContextTokenK.value = formData.apiContextLength / 1024;
    }
  },
  { deep: true }
);
</script>

<style lang="scss" scoped>
.settings-popover {
  width: 100%;
  padding: 12px;

  h3 {
    margin-top: 0;
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 500;
  }

  :deep(.arco-form-item) {
    margin-bottom: 16px;
  }

  .label-with-tooltip {
    display: flex;
    align-items: center;
    gap: 4px;

    .arco-icon {
      font-size: 14px;
      color: #86909c;
      cursor: pointer;

      &:hover {
        color: #165dff;
      }
    }
  }

  .param-control {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;

    :deep(.arco-slider) {
      flex: 1;
      min-width: 150px;
    }

    :deep(.arco-input-number) {
      width: 80px;
      flex-shrink: 0;
    }
  }
}
</style>