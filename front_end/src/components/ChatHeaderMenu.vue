<template>
  <div class="chat-header-menu">
    <div class="chat-title-container">
      <div class="chat-title">{{ currentChatTitle }}</div>
      <div class="current-model">
        当前模型：{{ currentActiveModelName }}
      </div>
    </div>
    <div class="icon-actions">
      <div style="margin-right: 10px;">{{ userInfo.username }}</div>
      <icon-settings class="icon-list" @click="openFullscreenView" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { IconSettings } from '@arco-design/web-vue/es/icon';
import { ref, computed, watch, onMounted, onActivated, onUnmounted } from 'vue';
import routeController from '@/controller/router';
import { useChatSetting } from '@/store/useChatSetting';
import { storeToRefs } from 'pinia';
import { useHomeChat } from '@/store/useHomeChat';
import { useAdvanceSettings } from '@/store/useAdvanceSettings';
import urlResquest from '@/services/urlConfig';
import { useUser } from '@/store/useUser';
import { useRoute } from 'vue-router';

const { chatId, historyList } = storeToRefs(useHomeChat());
const { userInfo } = storeToRefs(useUser());
const route = useRoute();

const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { setAllChatSettingConfigured, setActiveChatSetting } = useChatSetting();


const { updateSettings } = useAdvanceSettings();

const { changePage } = routeController();

// 当前活跃模型名称
const currentActiveModelName = computed(() => {
  const activeModel = chatSettingConfigured.value.find(item => item.active === true);
  return activeModel?.modelName || activeModel?.apiModelName || '正在加载模型...';
});

const currentChatTitle = computed(() => {
  const currentChatTitle = historyList.value.find(item => item.qa_id === chatId.value);
  return currentChatTitle?.title || '新对话';
});

const isFullscreenViewOpen = ref(false);
const modelList = ref([]);

// 打开全屏视图
function openFullscreenView() {
  isFullscreenViewOpen.value = true;
  // 根据用户权限决定跳转目标
  if (userInfo.value?.role === 'admin' || userInfo.value?.role === 'superadmin') {
    // 管理员跳转到模型管理页面
    changePage('/fullscreen-view/model-management');
  } else {
    // 普通用户跳转到设置页面根路径，显示空白页面
    changePage('/fullscreen-view');
  }
}

// 获取模型列表
const fetchModelList = async () => {
  try {
    // 根据用户角色决定获取哪些模型
    if (userInfo.value?.role === 'admin' || userInfo.value?.role === 'superadmin') {
      // 管理员获取所有模型列表
      console.log('管理员开始获取模型列表...');
      const response = await urlResquest.getModelList({}, {});
      console.log('管理员模型列表API响应:', response);
      
      if (response && response.data) {
        modelList.value = response.data.configs;
        console.log('管理员获取到的模型列表:', modelList.value);
        console.log('检查活跃模型状态:');
        modelList.value.forEach((model, index) => {
          console.log(`  模型${index + 1}: ${model.service_name}, is_active: ${model.is_active}`);
        });
        
        // 将API返回的模型数据映射到chatSettingConfigured格式，管理员根据后端is_active字段判断
        updateChatSettingWithModelList(modelList.value, false);
      } else {
        console.error('管理员获取模型列表失败:', response);
      }
    } else {
      // 普通用户固定使用admin账户设置的活跃模型
      const response = await urlResquest.getActiveModel({}, {});
      console.log('普通用户活跃模型API响应:', response);
      console.log('API响应状态码:', response?.code);
      console.log('API响应数据:', response?.data);
      
      if (response && response.code === 200 && response.data) {
        console.log('普通用户获取到管理员的活跃模型:', response.data);
        // 将活跃模型映射到chatSettingConfigured格式，普通用户获取的就是活跃模型，强制设置为active
        updateChatSettingWithModelList([response.data], true);
      } else {
        console.error('获取管理员活跃模型失败:', response);
        console.error('API响应状态码:', response?.code);
        console.error('API响应消息:', response?.msg);
        
        // 设置错误状态，提示联系管理员
        setAllChatSettingConfigured([{
          modelType: 'error',
          modelName: '模型获取失败',
          apiModelName: '请联系管理员配置模型',
          active: true,
          apiKey: '',
          apiBase: '',
          chunkSize: 800,
          apiContextLength: 4096,
          maxToken: 1024,
          temperature: 0.5,
          top_P: 1.0,
          top_K: 40,
          context: 10,
          capabilities: {
            networkSearch: false,
            mixedSearch: false,
            onlySearch: false,
            rerank: false,
          }
        }]);
      }
    }
  } catch (error) {
    console.error('获取模型失败:', error);
    // 网络错误或其他异常，也设置一个错误提示状态
    setAllChatSettingConfigured([{
      modelType: 'error',
      modelName: '模型加载失败',
      apiModelName: '请检查网络连接',
      active: true,
      apiKey: '',
      apiBase: '',
      chunkSize: 800,
      apiContextLength: 4096,
      maxToken: 1024,
      temperature: 0.5,
      top_P: 1.0,
      top_K: 40,
      context: 10,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      }
    }]);
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models, forceActive = false) => {
  if (!models || models.length === 0) {
    console.log('没有模型数据');
    return;
  }

  console.log('开始处理模型数据:', models);
  console.log('是否强制设置为活跃:', forceActive);

  // 将API返回的模型映射为chatSettingConfigured格式
  const customModels = models.map(model => {
    console.log('处理单个模型数据:', model);
    
    const mappedModel = {
      modelType: model.model_endpoint || model.service_name || model.modelType || '',
      modelName: model.service_name || model.modelName || '未知模型',
      customId: model.config_id || model.customId || '',
      apiKey: model.api_key || model.apiKey || '',
      apiBase: model.api_proxy || model.apiBase || '',
      chunkSize: 800, // 使用默认值，因为后端没有这个字段
      apiModelName: model.service_name || model.apiModelName || model.modelName || '未知模型',
      serviceId: model.service_id || model.serviceId || '',
      apiContextLength: model.api_context_length || model.apiContextLength || 4096,
      maxToken: Math.floor((model.max_token || model.maxToken || 4096)),
      temperature: model.temperature || 0.5,
      top_P: model.top_p || model.top_P || 1.0,
      top_K: model.top_k || model.top_K || 40,
      context: model.context_length || model.context || 10,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      },
      active: forceActive || model.is_active === 1 || model.is_active === true || model.active === true, // 根据参数或后端数据设置活跃状态
      // 保存原始数据，以便后续可能需要
      originalData: { ...model }
    };
    
    console.log('映射后的模型:', mappedModel);
    console.log('用于验证的关键字段:');
    console.log('  - apiModelName:', mappedModel.apiModelName);
    console.log('  - modelName:', mappedModel.modelName);
    console.log('  - apiBase:', mappedModel.apiBase);
    console.log('  - apiKey:', mappedModel.apiKey);
    console.log('  - modelType:', mappedModel.modelType);
    console.log('  - active:', mappedModel.active);
    console.log('  - forceActive:', forceActive);
    console.log('  - model.is_active:', model.is_active);
    
    return mappedModel;
  });
  
  console.log('所有映射后的模型:', customModels);
  
  // 检查是否有活跃模型，如果没有则设置第一个为活跃
  const hasActiveModel = customModels.some(model => model.active);
  if (!hasActiveModel && customModels.length > 0) {
    console.log('没有找到活跃模型，将第一个模型设为活跃');
    customModels[0].active = true;
  }
  
  console.log('最终的模型列表（含活跃状态）:', customModels);
  
  // 更新chatSettingConfigured，使用新的批量设置函数
  setAllChatSettingConfigured([...customModels]);
};

// 监听路由变化 - 每当进入聊天页面都触发模型配置获取
watch(
  () => route.path,
  async (newPath, oldPath) => {
    console.log('路由变化:', oldPath, '->', newPath);
    
    // 判断是否切换到了聊天页面
    if (newPath === '/home' || newPath.includes('/home')) {
      console.log('检测到切换到聊天页面，强制获取最新模型配置');
      await forceRefreshModelConfiguration();
    }
  },
  { immediate: true }
);

// 监听用户信息变化 - 保持原有逻辑但加强
watch(
  userInfo,
  async (newUserInfo, oldUserInfo) => {
    console.log('用户信息变化:', oldUserInfo, '->', newUserInfo);
    
    if (newUserInfo && newUserInfo.userId) {
      // 检测是否是用户切换
      if (oldUserInfo && oldUserInfo.userId && oldUserInfo.userId !== newUserInfo.userId) {
        console.log('检测到用户切换，清理旧模型配置并重新获取');
        // 先清理旧的模型配置
        setAllChatSettingConfigured([]);
        
        // 延迟一点时间，确保其他组件也能响应用户信息变化
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      console.log('用户信息已加载，强制获取最新模型配置:', newUserInfo);
      await forceRefreshModelConfiguration();
    } else {
      console.log('用户信息不完整或已清空，清理模型配置');
      // 用户信息清空时也清理模型配置
      setAllChatSettingConfigured([]);
    }
  },
  { immediate: true, deep: true }
);

onMounted(async () => {
  console.log('=== ChatHeaderMenu组件已挂载 ===');
  console.log('挂载时用户信息:', userInfo.value);
  console.log('挂载时路由路径:', route.path);
  
  // 检查是否刚刚登录
  const justLoggedIn = localStorage.getItem('justLoggedIn');
  if (justLoggedIn === 'true') {
    console.log('检测到刚刚登录，清除标记并等待模型配置加载');
    localStorage.removeItem('justLoggedIn');
    
    // 等待登录页面的模型配置获取完成
    for (let i = 0; i < 30; i++) {
      const existingConfig = chatSettingConfigured.value;
      if (existingConfig && existingConfig.length > 0) {
        const activeModel = existingConfig.find(item => item.active === true);
        if (activeModel && activeModel.apiModelName && 
            activeModel.apiModelName !== '正在加载模型...' &&
            activeModel.modelName !== '模型获取失败') {
          console.log('登录时的模型配置已加载完成:', activeModel.apiModelName);
          return; // 已经有配置了，不需要重复获取
        }
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('等待3秒后登录时的模型配置仍未加载，将重新获取');
  }
  
  // 检测是否可能是登录后直接进入聊天页面
  const isDirectLoginEntry = !userInfo.value || !userInfo.value.userId;
  if (isDirectLoginEntry) {
    console.log('检测到可能是登录后直接进入，需要等待用户信息加载');
    
    // 等待用户信息加载的增强版本 - 最多等待5秒
    for (let i = 0; i < 50; i++) {
      if (userInfo.value && userInfo.value.userId) {
        console.log(`用户信息已加载 (等待了${i * 100}ms):`, userInfo.value);
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    if (!userInfo.value || !userInfo.value.userId) {
      console.error('等待5秒后仍未获取到用户信息');
    }
  }
  
  // 强制获取最新模型配置，不管任何条件
  await forceRefreshModelConfiguration();
});

// 组件激活时（keep-alive场景）
onActivated(async () => {
  console.log('=== ChatHeaderMenu组件已激活 ===');
  console.log('激活时用户信息:', userInfo.value);
  console.log('激活时路由路径:', route.path);
  
  // 每次激活都强制刷新模型配置
  await forceRefreshModelConfiguration();
});

// 监听页面可见性变化，处理浏览器标签页切换等情况
onMounted(() => {
  const handleVisibilityChange = async () => {
    if (!document.hidden) {
      console.log('=== 页面重新可见，检查模型配置 ===');
      // 页面重新可见时，检查并刷新模型配置
      await forceRefreshModelConfiguration();
    }
  };
  
  document.addEventListener('visibilitychange', handleVisibilityChange);
  
  // 组件卸载时清理监听器
  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  });
});

// 新增：强制刷新模型配置的函数 - 这是最核心的机制
const forceRefreshModelConfiguration = async () => {
  console.log('=== 开始强制刷新模型配置 ===');
  console.log('当前用户信息:', userInfo.value);
  console.log('当前路由:', route.path);
  
  // 检查是否已经有有效的模型配置（可能在登录时已获取）
  const existingConfig = chatSettingConfigured.value;
  if (existingConfig && existingConfig.length > 0) {
    const activeModel = existingConfig.find(item => item.active === true);
    if (activeModel && activeModel.apiModelName && 
        activeModel.apiModelName !== '正在加载模型...' &&
        activeModel.modelName !== '模型获取失败' &&
        activeModel.modelType !== 'error') {
      console.log('已存在有效模型配置，跳过重复获取:', activeModel.apiModelName);
      return;
    }
  }
  
  console.log('需要获取模型配置...');
  
  // 设置正在加载状态
  setAllChatSettingConfigured([{
    modelType: 'loading',
    modelName: '正在加载模型...',
    apiModelName: '正在加载模型...',
    active: true,
    apiKey: '',
    apiBase: '',
    chunkSize: 800,
    apiContextLength: 4096,
    maxToken: 1024,
    temperature: 0.5,
    top_P: 1.0,
    top_K: 40,
    context: 10,
    capabilities: {
      networkSearch: false,
      mixedSearch: false,
      onlySearch: false,
      rerank: false,
    }
  }]);
  
  // 多次尝试获取模型配置 - 最多尝试5次
  for (let i = 0; i < 5; i++) {
    console.log(`强制刷新: 第${i + 1}次尝试获取模型配置`);
    
    try {
      // 如果没有用户信息，等待一下
      if (!userInfo.value || !userInfo.value.userId) {
        console.log('等待用户信息加载...');
        await new Promise(resolve => setTimeout(resolve, 200));
        continue;
      }
      
      console.log('用户信息已加载，开始获取模型配置');
      await fetchModelList();
    
      // 验证获取结果
      const currentConfig = chatSettingConfigured.value;
      if (currentConfig && currentConfig.length > 0) {
        const activeModel = currentConfig.find(item => item.active === true);
        if (activeModel && activeModel.apiModelName && 
            activeModel.apiModelName !== '正在加载模型...' &&
            activeModel.modelName !== '模型获取失败') {
          console.log('强制刷新: 模型配置获取成功', activeModel);
          return; // 成功获取，退出循环
        }
      }
      
      console.log('强制刷新: 获取到的配置无效，继续重试');
    } catch (error) {
      console.error(`强制刷新: 第${i + 1}次获取失败:`, error);
    }
    
    // 等待一段时间再重试
    await new Promise(resolve => setTimeout(resolve, 300 * (i + 1))); // 递增等待时间
  }
  
  // 如果多次尝试仍失败，设置错误状态
  console.error('强制刷新: 多次尝试后仍无法获取有效模型配置');
  setAllChatSettingConfigured([{
    modelType: 'error',
    modelName: '模型获取失败',
    apiModelName: '请刷新页面重试',
    active: true,
    apiKey: '',
    apiBase: '',
    chunkSize: 800,
    apiContextLength: 4096,
    maxToken: 1024,
    temperature: 0.5,
    top_P: 1.0,
    top_K: 40,
    context: 10,
    capabilities: {
      networkSearch: false,
      mixedSearch: false,
      onlySearch: false,
      rerank: false,
    }
  }]);
};

// 保留原有的初始化函数作为备用
const initializeModelConfiguration = async () => {
  console.log('开始初始化模型配置...');
  
  // 直接调用强制刷新函数
  await forceRefreshModelConfiguration();
};

</script>

<style scoped>
.chat-header-menu {
  height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #D8D8D8;
  background-color: #F8F8F8;
}

.chat-title-container {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .chat-title {
    margin-right: 16px;
    font-size: 16px;
    font-weight: 500;
    color: #1a1a1a;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .current-model {
    font-size: 14px;
    color: #3491FA;
    font-weight: 500;
    background-color: #E8F7FF;
    padding: 4px 12px;
    border-radius: 4px;
  }
}

.icon-list {
  font-size: 16px;
  color: #4E5969;
  cursor: pointer;
  transition: all 0.3s;
}

.icon-list:hover {
  color: #3491FA;
  transform: scale(1.1);
}

.icon-actions {

  .arco-icon-settings {
    font-size: 20px;
  }
  display: flex;
  align-items: center;
}

:deep(.arco-select-view-suffix) {
  padding: 0px 0px;
}

/* 覆写 arco-select 样式 */
:deep(.arco-select-view-single) {

  background-color: #E8F7FF;
  color: #3491FA;
  padding: 4px 12px;
  font-weight: 500;
  padding: 0px 8px;
  border-color: #E8F7FF;
}

:deep(.arco-select-view-single:hover) {
  background-color: #D0EBFF !important;
  border-color: #3491FA !important;
}

:deep(.arco-select-view-value) {
  color: #3491FA;
  font-weight: 500;
  font-size: 14px;
  line-height: 24px;
}

:deep(.arco-select-arrow) {
  color: #3491FA;
  margin-top: -2px;
}

/* 确保下拉选项也使用相同的文字颜色 */
:deep(.arco-select-dropdown) {
  width: 100px;

  .arco-select-option {
    padding: 8px 12px;

    &.arco-select-option-active,
    &.arco-select-option-selected {
      color: #3491FA;
      background-color: #E8F7FF;
      border-radius: 4px;
    }

    &:hover {
      background-color: #E8F7FF;
    }
  }
}

/* 添加菜单容器样式 */
.menu-container {
  display: flex;
  align-items: center;
}
</style>
