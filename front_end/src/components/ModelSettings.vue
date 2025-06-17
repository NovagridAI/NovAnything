<template>
  <div class="model-settings">
    <div class="model-settings-header">
      <div class="model-settings-header-title">
        <span class="title-text">模型设置</span>
        <div class="action-buttons">
          <arco-button @click="cancelSettings" class="cancel-btn">
            取消
          </arco-button>
          <arco-button type="primary" @click="saveSettings" class="save-btn">
            保存设置
          </arco-button>
        </div>
      </div>
    </div>
    
    <arco-card :bordered="false">
      <arco-form ref="formRef" :model="formData" :rules="rules" layout="horizontal" :label-col-props="{ span: 4 }"
        :wrapper-col-props="{ span: 20 }" :label-align="'left'" :key="refreshKey">
        
        <arco-form-item field="serviceId" label="模型提供方：">
          <arco-select v-model="formData.serviceId" placeholder="请选择模型提供方" :disabled="isEditMode">
            <arco-option value="openai">OpenAI</arco-option>
            <arco-option value="ollama">Ollama</arco-option>
            <arco-option value="custom">自定义</arco-option>
          </arco-select>
        </arco-form-item>

        <arco-form-item field="apiKey" label="API密钥">
          <arco-input-password v-model="formData.apiKey" placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx" allow-clear />
        </arco-form-item>

        <arco-form-item field="apiBase" label="API路径">
          <arco-input v-model="formData.apiBase" placeholder="请输入API路径" />
        </arco-form-item>

        <arco-form-item field="modelName" label="模型名称">
          <arco-input v-model="formData.modelName" placeholder="请输入模型名称" />
        </arco-form-item>

        <arco-form-item field="apiContextLength" label="总Token数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">LLM输入和输出的总token数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="apiContextTokenK" :min="1" :max="10000" :step="1" />
              <arco-input-number v-model="apiContextTokenK" :min="1" :max="10000" :step="1" :precision="0" :hide-button="true">
                <template #append>K</template>
              </arco-input-number>
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="maxToken" label="输出Token数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">LLM输出的token数量上限. 最大值为: 总Token数量 / 4</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO" :step="1" />
              <arco-input-number v-model="formData.maxToken" :min="1" :max="formData.apiContextLength / TOKENRATIO" :step="1" :precision="0" :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="temperature" label="随机性">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">控制输出的随机性。较低值使输出更确定，较高值增加创意性</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.temperature" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="formData.temperature" :min="0" :max="1" :step="0.01" :precision="2" :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="top_P" label="累积概率阈值">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">限制词汇选择范围。较低值使输出更聚焦，较高值增加多样性</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.top_P" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="formData.top_P" :min="0" :max="1" :step="0.01" :precision="2" :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="top_K" label="检索结果数量上限">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">检索算法取所有文档分片里最相关的分片数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider v-model="formData.top_K" :min="1" :max="100" :step="1" />
              <arco-input-number v-model="formData.top_K" :min="1" :max="100" :step="1" :precision="0" :hide-button="true" />
            </div>
          </div>
        </arco-form-item>

        <arco-form-item field="context" label="上下文消息数量">
          <div class="token-input-wrapper">
            <div class="token-input-wrapper-tip">单轮对话中保留的历史消息数量上限</div>
            <div class="token-input-wrapper-input">
              <arco-slider 
                v-model="formData.context" 
                :min="0" 
                :max="11" 
                :step="1" 
                :format-tooltip="sliderFormatter"
              />
              <arco-input 
                disabled 
                v-model="contextDisplayValue" 
                :hide-button="true" 
              />
            </div>
          </div>
        </arco-form-item>

      </arco-form>
    </arco-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Message } from '@arco-design/web-vue';
import urlResquest from '@/services/urlConfig';
import { useUser } from '@/store/useUser';
import { storeToRefs } from 'pinia';

const route = useRoute();
const router = useRouter();
const { userInfo } = storeToRefs(useUser());

const formRef = ref(null);
const TOKENRATIO = 4;
const refreshKey = ref(0);

// 表单数据
const formData = reactive({
  modelName: '',
  serviceId: 'openai',
  apiKey: '',
  apiBase: '',
  modelType: '',
  apiContextLength: 4096,
  maxToken: 1024,
  temperature: 0.5,
  top_P: 1.0,
  top_K: 40,
  context: 10,
});

// 上下文长度，单位k
const apiContextTokenK = ref(4);

// 是否是编辑模式
const isEditMode = computed(() => !!route.query.id);
const editingModelId = computed(() => route.query.id || '');

// 上下文显示值
const contextDisplayValue = computed({
  get: () => formData.context >= 11 ? '无限制' : formData.context.toString(),
  set: (val) => {
    formData.context = val === '无限制' ? 11 : parseInt(val);
  }
});

// 验证规则
const rules = {
  modelName: [{ required: true, message: '请输入模型名称' }],
  serviceId: [{ required: true, message: '请选择模型提供方' }],
  apiKey: [{ required: true, message: '请输入API密钥' }],
  apiBase: [{ required: true, message: '请输入API路径' }],
  apiContextLength: [{ required: true, message: '请设置总Token数量' }],
  maxToken: [{ required: true, message: '请设置输出Token数量' }],
  temperature: [{ required: true, message: '请设置随机性' }],
  top_P: [{ required: true, message: '请设置累积概率阈值' }],
  top_K: [{ required: true, message: '请设置Top K值' }]
};

// 上下文条数格式化
const sliderFormatter = (value) => {
  return value >= 11 ? '无限制' : value;
};

// 监听apiContextTokenK变化
watch(
  () => apiContextTokenK.value,
  () => {
    formData.apiContextLength = apiContextTokenK.value * 1024;
  }
);

// 监听apiContextLength变化
watch(
  () => formData.apiContextLength,
  () => {
    apiContextTokenK.value = formData.apiContextLength / 1024;
  }
);

// 监听路由变化，重新获取数据
watch(
  () => route.fullPath,
  async (newPath, oldPath) => {
    console.log('路由完整路径变化:', { newPath, oldPath });
    console.log('当前查询参数:', route.query);
    console.log('编辑模式ID:', route.query.id);
    
    if (route.query.id) {
      console.log('检测到编辑模式，模型ID:', route.query.id);
      // 重置表单数据
      Object.assign(formData, {
        modelName: '',
        serviceId: 'openai',
        apiKey: '',
        apiBase: '',
        modelType: '',
        apiContextLength: 4096,
        maxToken: 1024,
        temperature: 0.5,
        top_P: 1.0,
        top_K: 40,
        context: 10,
      });
      
      await fetchModelDetail();
    } else {
      // 非编辑模式，重置为默认值
      console.log('切换到新建模式，重置表单');
      Object.assign(formData, {
        modelName: '',
        serviceId: 'openai',
        apiKey: '',
        apiBase: '',
        modelType: '',
        apiContextLength: 4096,
        maxToken: 1024,
        temperature: 0.5,
        top_P: 1.0,
        top_K: 40,
        context: 10,
      });
      apiContextTokenK.value = 4;
    }
  },
  { immediate: true }
);

// 获取模型详情（编辑模式）
const fetchModelDetail = async () => {
  // 直接从路由获取ID，避免计算属性可能的延迟
  const modelId = route.query.id as string;
  console.log('fetchModelDetail 被调用');
  console.log('当前路由:', route.fullPath);
  console.log('路由查询参数:', route.query);
  console.log('模型ID:', modelId);
  console.log('editingModelId.value:', editingModelId.value);
  
  if (!modelId) {
    console.log('无模型ID，跳过获取详情');
    return;
  }
  
  console.log('开始获取模型详情，模型ID:', modelId);
  
  try {
    const requestParams = { config_id: modelId };
    console.log('API请求参数:', requestParams);
    
    const response = await urlResquest.getModelDetail(requestParams);
    console.log('API响应完整信息:', JSON.stringify(response, null, 2));
    
    if (response && response.code === 200 && response.data) {
      const model = response.data;
      console.log('解析到的模型数据:', JSON.stringify(model, null, 2));
      
      // 直接设置表单数据
      formData.modelName = model.service_name || '';
      formData.serviceId = model.service_id || 'openai';
      formData.apiKey = model.api_key || '';
      formData.apiBase = model.api_proxy || '';
      formData.modelType = model.model_endpoint || model.service_name || '';
      formData.apiContextLength = model.api_context_length || 4096;
      formData.maxToken = model.max_token || 1024;
      formData.temperature = model.temperature || 0.5;
      formData.top_P = model.top_p || 1.0;
      formData.top_K = model.top_k || 40;
      formData.context = model.context_length || 10;
      
      // 更新Token K值
      apiContextTokenK.value = formData.apiContextLength / 1024;
      
      console.log('=== 数据设置完成后的表单状态 ===');
      console.log('formData.modelName:', formData.modelName);
      console.log('formData.serviceId:', formData.serviceId);
      console.log('formData.apiKey:', formData.apiKey);
      console.log('formData.apiBase:', formData.apiBase);
      console.log('完整formData:', JSON.stringify(formData, null, 2));
      
      Message.success('模型配置加载成功');
    } else {
      console.error('API响应错误:', response);
      Message.error(response?.msg || '获取模型详情失败：响应数据无效');
    }
  } catch (error) {
    console.error('API调用失败:', error);
    Message.error(`获取模型详情失败: ${error.message || error}`);
  }
};

// 保存设置
const saveSettings = async () => {
  try {
    await formRef.value.validate();
    
    const modelData = {
      service_name: formData.modelName,
      service_id: formData.serviceId,
      api_key: formData.apiKey,
      api_proxy: formData.apiBase,
      model_endpoint: formData.modelType || formData.modelName,
      api_context_length: formData.apiContextLength,
      max_token: formData.maxToken,
      temperature: formData.temperature,
      top_p: formData.top_P,
      top_k: formData.top_K,
      context_length: formData.context,
      request_format: "openAI",
      is_global: userInfo.value.role === 'superadmin' ? true : false
    };

    console.log('准备保存的模型数据:', modelData);

    if (isEditMode.value) {
      // 更新模型
      modelData.config_id = editingModelId.value;
      console.log('更新模型，ID:', editingModelId.value);
      const response = await urlResquest.updateModel(modelData);
      console.log('更新模型响应:', response);
      if (response && response.code === 200) {
        Message.success('模型保存成功');
        router.push('/fullscreen-view/model-management');
      } else {
        Message.error(response?.msg || '保存失败');
      }
    } else {
      // 创建新模型
      console.log('创建新模型');
      const response = await urlResquest.createModel(modelData);
      console.log('创建模型响应:', response);
      if (response && response.code === 200) {
        Message.success('模型保存成功');
        router.push('/fullscreen-view/model-management');
      } else {
        Message.error(response?.msg || '保存失败');
      }
    }
  } catch (error) {
    console.error('表单验证失败', error);
    Message.error('表单验证失败');
  }
};

// 取消设置
const cancelSettings = () => {
  router.push('/fullscreen-view/model-management');
};

onMounted(async () => {
  // 路由监听器会自动处理编辑模式的数据加载
  console.log('ModelSettings组件已挂载');
  console.log('当前路由:', route.fullPath);
  console.log('路由查询参数:', route.query);
  console.log('编辑模式:', isEditMode.value);
  console.log('模型ID:', editingModelId.value);
  console.log('初始表单数据:', JSON.stringify(formData, null, 2));
  
  // 如果是编辑模式，手动调用一次数据获取
  if (isEditMode.value) {
    console.log('onMounted: 检测到编辑模式，手动获取模型详情');
    await fetchModelDetail();
  }
});
</script>

<style scoped lang="scss">
.model-settings {
  padding: 20px;
  margin: 0 50px;
}

.model-settings-header {
  margin-bottom: 20px;
  
  .model-settings-header-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-left: 16px;
    
    .title-text {
      font-size: 24px;
      color: #1a1a1a;
    }
    
    .action-buttons {
      display: flex;
      gap: 12px;
      margin-right: 16px;
      
      .cancel-btn {
        min-width: 80px;
      }
      
      .save-btn {
        min-width: 100px;
      }
    }
  }
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
  flex: 1;
  line-height: 1.4;
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
</style> 