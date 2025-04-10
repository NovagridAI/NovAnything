<template>
  <div class="chat-setting-page">
    <div class="chat-setting-page-header">
      <div class="chat-setting-page-header-title">
        模型设置
        <span v-if="saveStatus" class="save-status" :class="saveStatus.type">
          {{ saveStatus.message }}
          <icon-loading v-if="saveStatus.type === 'saving'" />
        </span>
      </div>
    </div>
    <arco-card :bordered="false">
      <arco-form ref="formRef" :model="formData" :rules="rules" layout="horizontal" :label-col-props="{ span: 4 }"
        :wrapper-col-props="{ span: 20 }" :label-align="'left'" @submit="onSubmit">
        <arco-form-item field="serviceId" label="模型提供方：">
          <arco-select v-model="formData.serviceId" placeholder="请选择模型提供方" @change="selectChange">
            <arco-option v-for="item of chatSettingConfigured" :key="item.serviceId" :value="item.serviceId">
              {{ item.apiModelName }} ({{ item.serviceId }})
            </arco-option>
          </arco-select>
          <arco-button style="margin-left: 10px;" type="primary" @click="showAddModelDialog">
            <IconPlus />
            添加新模型
          </arco-button>
        </arco-form-item>

        <arco-form-item field="apiKey" label="API密钥">
          <arco-input-password v-model="formData.apiKey" placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx" allow-clear />
        </arco-form-item>

        <arco-form-item field="apiBase" label="API路径">
          <arco-input v-model="formData.apiBase" placeholder="请输入API路径" />
        </arco-form-item>

        <arco-form-item field="modelType" label="模型名称">
          <arco-input v-model="formData.modelType" placeholder="请输入模型名称" />
          <!-- <arco-select v-else v-model="formData.apiModelName"
            :options="openAIModelDefault.map(item => ({ value: item }))" @change="openAIModelSelect">
            <template #dropdown-render="{ menu }">
              <div>{{ menu }}</div>
              <arco-divider style="margin: 4px 0" />
              <arco-space style="padding: 4px 8px">
                <arco-input ref="inputRef" v-model="name" placeholder="输入模型名称" />
                <arco-button type="text" @click="addItem">添加模型</arco-button>
              </arco-space>
            </template>
          </arco-select> -->
        </arco-form-item>

        <arco-form-item field="apiContextLength" label="总Token数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">LLM输入和输出的总token数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="apiContextTokenK" :min="1"
                :max="openAIModelMax || 200" :step="1" />
              <arco-input-number v-model="apiContextTokenK" :min="1"
                :max="openAIModelMax || 200" :step="1" :precision="0" :hide-button="true">
                <template #append>K</template>
              </arco-input-number>
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="maxToken" label="输出Token数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">LLM输出的token数量上限. 最大值为: 总Token数量 / 4</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO"
                :step="1" />
              <arco-input-number v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO"
                :step="1" :precision="0" :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="temperature" label="随机性">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">控制输出的随机性。较低值使输出更确定，较高值增加创意性</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.temperature" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="formData.temperature" :min="0" :max="1" :step="0.01" :precision="2"
                :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="top_P" label="累积概率阈值">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">限制词汇选择范围。较低值使输出更聚焦，较高值增加多样性</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.top_P" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="formData.top_P" :min="0" :max="1" :step="0.01" :precision="2"
                :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="top_K" label="检索结果数量上限">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">检索算法取所有文档分片里最相关的分片数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.top_K" :min="1" :max="100" :step="1" />
              <arco-input-number v-model="formData.top_K" :min="1" :max="100" :step="1" :precision="0"
                :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="context" label="上下文消息数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">单轮对话中保留的历史消息数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.context" :min="0" :max="11" :step="1" :format-tooltip="sliderFormatter" />
              <arco-input disabled v-model="contextDisplayValue" :min="0" :max="11" :step="1" :precision="0"
              :hide-button="true" />
            </div>
          </div>
        </arco-form-item>
        <arco-form-item v-if="isCreatingNewModel">
          <arco-button type="primary" html-type="submit">保存模型</arco-button>
        </arco-form-item>

        <arco-form-item v-else>
          <arco-space>
            <!-- <arco-button type="primary" @click="saveSettings">保存设置</arco-button> -->
            <!-- <arco-button @click="resetSettings">重置</arco-button> -->
          </arco-space>
        </arco-form-item>
      </arco-form>
    </arco-card>
    <!-- <ChatSettingForm /> -->

    <arco-modal v-model:visible="addModelDialogVisible" title="自定义模型" @cancel="cancelAddModel" @ok="confirmAddModel"
      :mask-closable="false">
      <arco-form ref="addModelFormRef" :model="newModelForm" :rules="newModelRules" layout="vertical">
        <arco-form-item field="serviceName" label="服务商名称">
          <arco-input v-model="newModelForm.serviceName" placeholder="请输入模型名称-必填" />
        </arco-form-item>
        <arco-form-item field="serviceId" label="服务商ID">
          <arco-input v-model="newModelForm.serviceId" placeholder="请输入模型名称-必填" />
        </arco-form-item>
        <arco-form-item field="request_format" label="请求格式">
          <arco-select disabled v-model="newModelForm.request_format" default-value="openAI" placeholder="OpenAI">
            <arco-option value="openAI">OpenAI</arco-option>
          </arco-select>
        </arco-form-item>

        <!-- <arco-form-item field="serviceType" label="接口方式">
          <arco-select v-model="newModelForm.serviceType" placeholder="OpenAI">
            <arco-option value="OpenAI">OpenAI</arco-option>
            <arco-option value="Custom">自定义</arco-option>
          </arco-select>
        </arco-form-item> -->

        <arco-form-item field="apiKey" label="API 密钥">
          <arco-input-password v-model="newModelForm.apiKey" placeholder="请输入API密钥" allow-clear />
        </arco-form-item>

        <arco-form-item field="apiBase" label="API路径">
          <arco-input v-model="newModelForm.apiBase" placeholder="例如: https://api.openai.com/v1" />
        </arco-form-item>

        <arco-form-item field="modelEndpoint" label="模型名称">
          <arco-input v-model="newModelForm.modelEndpoint" placeholder="例如: gpt-3.5-turbo" />
        </arco-form-item>
      </arco-form>
    </arco-modal>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onBeforeMount, onMounted, nextTick, computed } from 'vue';
import { Message } from '@arco-design/web-vue';
import { useChatSetting } from '@/store/useChatSetting';
import { getLanguage } from '@/language';
import { storeToRefs } from 'pinia';
import ChatSettingForm from './ChatSettingForm.vue';
import urlResquest from '@/services/urlConfig';
import { IconPlus, IconLoading } from '@arco-design/web-vue/es/icon';
import { debounce } from 'lodash-es';
import { useUser } from '@/store/useUser';

const common = getLanguage().common;
const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { setChatSettingConfigured, openAISettingMap, setAllChatSettingConfigured, setActiveChatSetting } = useChatSetting();
const { userInfo } = storeToRefs(useUser());

console.log(userInfo.value, 'userInfo')
console.log(chatSettingConfigured.value, 'chatSettingConfigured')

const formRef = ref(null);
const TOKENRATIO = 4;

// 表单数据
const formData = reactive({
  modelType: '',
  modelName: '',
  apiKey: '',
  apiBase: '',
  apiModelName: '',
  apiContextLength: 4096,
  maxToken: 1024,
  temperature: 0.5,
  top_P: 1.0,
  top_K: 40,
  context: 10,
  capabilities: {}
});

// OpenAI模型相关
const openAIModelDefault = ref([]);
const inputRef = ref();
const name = ref('');
let index = 0;
const openAIModelMax = ref(200);

// 上下文长度，单位k
const apiContextTokenK = ref(4);

// 添加一个标志来跟踪是否是首次加载
const isInitialLoad = ref(true);

// 添加保存状态
const saveStatus = ref(null);

// 上下文显示值
const contextDisplayValue = computed({
  get: () => formData.context >= 11 ? '无限制' : formData.context,
  set: (val) => {
    formData.context = val;
  }
});

// 验证规则
const rules = {
  modelType: [{ message: '请选择模型提供方' }],
  modelName: [{ message: '请输入模型名称' }],
  apiKey: [{ message: '请输入API密钥' }],
  apiBase: [{ message: '请输入API路径' }],
  apiModelName: [{ message: '请输入模型名称' }],
  apiContextLength: [{ message: '请设置总Token数量' }],
  maxToken: [{ message: '请设置输出Token数量' }],
  temperature: [{ message: '请设置随机性' }],
  top_P: [{ message: '请设置累积概率阈值' }],
  top_K: [{ message: '请设置Top K值' }]
};

// 添加OpenAI模型
const addItem = (e) => {
  e.preventDefault();
  openAIModelDefault.value.push(name.value || `New item ${(index += 1)}`);
  name.value = '';
  setTimeout(() => {
    inputRef.value?.focus();
  }, 0);
};

// 选择OpenAI模型
const openAIModelSelect = (value) => {
  const curContextLength = openAISettingMap.get(value)?.apiContextLength;
  if (curContextLength) {
    apiContextTokenK.value = curContextLength / 1024;
    openAIModelMax.value = curContextLength / 1024;
  } else {
    apiContextTokenK.value = 4;
  }
};

// 上下文条数格式化
const sliderFormatter = (value) => {
  return value >= 11 ? '无限制' : value;
};

// 添加防抖的updateModel函数
const updateModel = debounce(async () => {
  // 如果是首次加载或没有选择模型或者是正在创建新模型，则不更新
  if (isInitialLoad.value || !formData.serviceId || isCreatingNewModel.value) {
    console.log('跳过更新', isInitialLoad.value ? '首次加载' : '其他原因');
    return;
  }

  try {
    // 设置保存状态为保存中
    saveStatus.value = { type: 'saving', message: '保存中' };

    console.log('准备更新模型:', formData.customId);
    // 准备更新模型的数据
    const modelData = {
      config_id: formData.customId,
      service_name: formData.modelName,
      max_token: formData.maxToken,
      api_key: formData.apiKey,
      api_proxy: formData.apiBase,
      model_endpoint: formData.modelType,
      api_context_length: formData.apiContextLength,
      temperature: formData.temperature,
      top_P: formData.top_P,
      top_k: formData.top_K,
      context_length: formData.context,
      // 其他可能需要的字段
    };

    // 调用API更新模型
    const response = await urlResquest.updateModel(modelData);

    if (response && response.code === 200) {
      console.log('模型更新成功');
      fetchModelList();
      // 设置保存状态为已保存
      saveStatus.value = { type: 'success', message: '已保存' };

      // 不再设置定时器清除状态
    } else {
      console.error('更新模型失败:', response?.msg);
      // 设置保存状态为失败
      saveStatus.value = { type: 'error', message: '保存失败' };

      // 不再设置定时器清除状态
    }
  } catch (error) {
    console.error('更新模型请求失败:', error);
    // 设置保存状态为失败
    saveStatus.value = { type: 'error', message: '保存失败' };

    // 不再设置定时器清除状态
  }
}, 1000); // 1秒的防抖延迟

// 监听表单数据变化，触发更新
watch(
  () => ({
    apiKey: formData.apiKey,
    apiBase: formData.apiBase,
    apiModelName: formData.apiModelName,
    apiContextLength: formData.apiContextLength,
    temperature: formData.temperature,
    top_P: formData.top_P,
    maxToken: formData.maxToken,
    modelType: formData.modelType,
    top_K: formData.top_K,
    context: formData.context
  }),
  () => {
    // 当表单数据变化时，调用防抖的updateModel函数
    if (!isInitialLoad.value) {
      updateModel();
    } else {
      console.log('首次加载，跳过更新');
    }
  },
  { deep: true }
);

// 选择模型类型
const selectChange = (value) => {
  console.log('select', value);
  openAIModelMax.value = 200;

  setActiveChatSetting(value);
  isInitialLoad.value = true;
  Object.assign(formData, chatSettingConfigured.value.find(item => item.serviceId === value));
  nextTick(() => {
    isInitialLoad.value = false;
  });

  // 选择模型后不需要立即更新，因为用户可能会继续修改其他字段
  // 如果需要立即更新，可以取消下面这行的注释
  // updateModel.cancel(); // 取消之前的防抖
};

// 保存设置
const saveSettings = async () => {
  try {
    await formRef.value.validate();
    // 保存设置的逻辑
    Message.success('设置已保存');
  } catch (error) {
    console.error('表单验证失败', error);
  }
};

// 重置设置
const resetSettings = () => {
  initForm();
  Message.info('设置已重置');
};

// 提交自定义模型
const onSubmit = async () => {
  try {
    await formRef.value.validate();
    setChatSettingConfigured(formData);
    Message.success('添加成功');
  } catch (error) {
    console.error('表单验证失败', error);
  }
};

// 初始化表单
const initForm = () => {
  // 设置isInitialLoad为true，防止初始化触发更新
  isInitialLoad.value = true;

  const activeForm = { ...chatSettingConfigured.value.find(item => item.active === true) };
  Object.assign(formData, activeForm);

  // 设置一个较长的延时，确保所有初始化操作完成后再将isInitialLoad设为false
  nextTick(() => {
    console.log('初始化完成，允许更新');
    isInitialLoad.value = false;
  }, 1500);
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
    Message.error('获取模型列表失败');
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models) => {
  if (!models || models.length === 0) return;

  // 保留原有的openAI和ollama配置
  const existingConfigs = chatSettingConfigured.value.filter(
    config => config.modelType === 'openAI' || config.modelType === 'ollama'
  );

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
      serviceId: model.service_id,
      apiContextLength: model.api_context_length || 4096,
      maxToken: Math.floor((model.max_token || 4096)),
      temperature: model.temperature || 0.5,
      top_P: model.top_P || 1.0,
      top_K: model.top_k || 40,
      context: model.context_length || 10,
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
  console.log(customModels, 'customModels')
  // 更新chatSettingConfigured，使用新的批量设置函数
  setAllChatSettingConfigured([...customModels]);
};

// 加载OpenAI模型列表
onBeforeMount(() => {
  openAIModelDefault.value = [...openAISettingMap.keys()];
  initForm();
});

// 在组件挂载时获取模型列表
onMounted(() => {
  // 确保isInitialLoad为true
  isInitialLoad.value = true;

  fetchModelList();

  // 确保在获取模型列表后再将isInitialLoad设为false
  setTimeout(() => {
    console.log('组件挂载完成，允许更新');
    isInitialLoad.value = false;
  }, 2000);
});

// 添加一个计算属性来判断是否正在创建新模型
const isCreatingNewModel = computed(() => {
  return formData.modelType === '自定义模型配置' ||
    (modelList.value && modelList.value.length > 0 &&
      !modelList.value.some(model => model.config_id === formData.customId));
});

// 添加新模型相关状态
const addModelDialogVisible = ref(false);
const addModelFormRef = ref(null);
const newModelForm = reactive({
  serviceName: '',
  serviceId: '',
  apiKey: '',
  apiBase: '',
  modelEndpoint: '',
  request_format: 'openAI'
});

// 新模型表单验证规则
const newModelRules = {
  serviceName: [{ required: true, message: '请输入服务商名称' }],
  serviceId: [{ required: true, message: '请输入服务商ID' }],
  apiKey: [{ required: true, message: '请输入API Key' }],
  apiBase: [{ required: true, message: '请输入API接口地址' }],
  modelEndpoint: [{ required: true, message: '请输入模型endpoint' }]
};

// 显示添加模型对话框
const showAddModelDialog = () => {
  console.log(chatSettingConfigured.value, 'chatSettingConfigured')
  addModelDialogVisible.value = true;
};

// 取消添加模型
const cancelAddModel = () => {
  addModelDialogVisible.value = false;
  // 重置表单
  Object.keys(newModelForm).forEach(key => {
    newModelForm[key] = key === 'serviceType' ? 'OpenAI' : '';
  });
};

// 确认添加模型
const confirmAddModel = async () => {
  try {
    // 验证表单
    await addModelFormRef.value.validate();

    console.log(newModelForm, 'newModelForm')
    // 创建新模型参数
    const modelData = {
      service_name: newModelForm.serviceName,
      service_id: newModelForm.serviceId,
      api_key: newModelForm.apiKey,
      api_proxy: newModelForm.apiBase,
      model_endpoint: newModelForm.modelEndpoint,
      request_format: "openAI",
      // 其他默认参数
      creativity: 1.0,
      thinking_depth: 1.0,
      expression_style: 1.0,
      vocabulary_richness: 1.0,
      token_limit: 4096,
      is_global: userInfo.value.role === 'superadmin' ? true : false
    };

    // 显示加载状态
    const loadingMessage = Message.loading({
      content: '正在创建模型...',
      duration: 0
    });

    try {
      // 调用API创建模型
      const response = await urlResquest.createModel(modelData);

      // 关闭加载提示
      loadingMessage.close();

      if (response && response.code === 200) {
        Message.success('模型添加成功');
        addModelDialogVisible.value = false;

        // 重新获取模型列表
        await fetchModelList();

        // 重置表单
        Object.keys(newModelForm).forEach(key => {
          newModelForm[key] = key === 'serviceType' ? 'OpenAI' : '';
        });
      } else {
        Message.error(response?.msg || '添加模型失败');
      }
    } catch (error) {
      // 关闭加载提示
      loadingMessage.close();
      console.error('创建模型失败:', error);
      Message.error(error?.msg || '创建模型请求失败，请检查网络连接');
    }
  } catch (error) {
    console.error('表单验证失败', error);
    // 表单验证失败时不关闭对话框，让用户修正输入
  }
};
</script>

<style scoped>
.chat-setting-page {
  padding: 20px;
  margin: 0 200px;
}

.chat-setting-page-header {
  font-size: 24px;
  color: #1a1a1a;
  margin-left: 16px;
}

/* 添加新的样式 */
:deep(.arco-form-item) {
  border-bottom: 1px solid #D8D8D8;
  padding-bottom: 16px;
  margin-bottom: 16px;
}

/* 设置表单标签样式 */
:deep(.arco-form-item-label-col > label) {
  font-size: 14px;
  font-weight: 500;
  color: #000000;
}

/* 最后一个表单项不需要边框 */
:deep(.arco-form-item:last-child) {
  border-bottom: none;
}

.token-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.token-input-wrapper-tip {
  font-size: 14px;
  color: #767676;
  user-select: text;
  flex:1;
}

.token-input-wrapper-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.token-input-wrapper .arco-slider {
  flex: 1;
  max-width: 200px;
  min-width: 200px;
  width: 100%;
}

.token-input-wrapper .arco-input-number {
  width: 100px;
  flex-shrink: 0;
}

.token-input-wrapper .arco-input-wrapper {
  width: 100px;
  flex-shrink: 0;
}

.content-length-ollama-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
  user-select: text;
}

.add-new-model-btn {
  cursor: pointer;
  color: #3c87ff;
  font-size: 14px;
  padding-left: 10px;
  transition: color 0.3s ease;

  &:hover {
    color: #165dff;
  }
}

.save-status {
  font-size: 14px;
  margin-left: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.save-status.saving {
  color: #165dff;
}

.save-status.success {
  color: #00b42a;
}

.save-status.error {
  color: #f53f3f;
}
</style>
