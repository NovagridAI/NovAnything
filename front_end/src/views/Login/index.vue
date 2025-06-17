<template>
  <div class="login-container">
    <div class="login-box">
      <!-- 登录图标 -->
      <div class="login-icon">
        <icon-lock />
      </div>
      
      <h2>登录</h2>
      <p class="subtitle">输入账号和密码登录</p>

      <arco-form
        :model="formState"
        name="basic"
        layout="vertical"
        :style="{ width: '100%' }"
        @submit="onFinish"
      >
        <arco-form-item
          field="username"
          :rules="[{ required: true, message: '请输入账号' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <arco-input 
            v-model="formState.username" 
            placeholder="Email"
            :style="{ backgroundColor: 'var(--color-fill-2)' }"
            size="large"
            allow-clear
            autocomplete="email"
          >
            <template #prefix>
              <icon-email />
            </template>
          </arco-input>
        </arco-form-item>

        <arco-form-item
          field="password"
          :rules="[{ required: true, message: '请输入密码' }]"
          :validate-trigger="['change', 'blur']"
          hide-label
        >
          <arco-input-password 
            v-model="formState.password" 
            placeholder="Password"
            :style="{ backgroundColor: 'var(--color-fill-2)' }"
            size="large"
            allow-clear
            autocomplete="current-password"
          >
            <template #prefix>
              <icon-lock />
            </template>
          </arco-input-password>
        </arco-form-item>

        <arco-form-item>
          <arco-button type="primary" html-type="submit" long size="large">
            登录
          </arco-button>
        </arco-form-item>
      </arco-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useUser } from '@/store/useUser';
import { useChatSetting } from '@/store/useChatSetting';
import { storeToRefs } from 'pinia';
import { IconEmail, IconLock } from '@arco-design/web-vue/es/icon';
import { Message } from '@arco-design/web-vue';
import urlRequest from '@/services/urlConfig';
import Cookies from 'js-cookie';

const router = useRouter();
const { setUserInfo } = useUser();
const { userInfo } = storeToRefs(useUser());
const { setAllChatSettingConfigured } = useChatSetting();
const formState = reactive({
  username: '',
  password: ''
});

// 登录时直接获取模型配置的函数
const fetchModelConfigOnLogin = async (userData: any) => {
  try {
    console.log('开始获取模型配置，用户角色:', userData.role);
    
    let modelList = [];
    
    // 根据用户角色决定获取哪些模型
    if (userData.role === 'admin' || userData.role === 'superadmin') {
      // 管理员获取所有模型列表
      console.log('管理员获取所有模型列表...');
      const response = await urlRequest.getModelList({}, {});
      console.log('管理员模型列表API响应:', response);
      
      if (response && response.data) {
        modelList = response.data.configs || [];
        console.log('管理员获取到的模型列表:', modelList);
        
        // 管理员模型配置，根据后端is_active字段判断
        updateChatSettingWithModelList(modelList, false);
      } else {
        console.error('管理员获取模型列表失败:', response);
        throw new Error('获取模型列表失败');
      }
    } else {
      // 普通用户获取管理员设置的活跃模型
      console.log('普通用户获取活跃模型...');
      const response = await urlRequest.getActiveModel({}, {});
      console.log('普通用户活跃模型API响应:', response);
      
      if (response && response.code === 200 && response.data) {
        console.log('普通用户获取到管理员的活跃模型:', response.data);
        // 普通用户获取的就是活跃模型，强制设置为active
        updateChatSettingWithModelList([response.data], true);
      } else {
        console.error('获取管理员活跃模型失败:', response);
        throw new Error('获取活跃模型失败');
      }
    }
    
    console.log('登录时模型配置获取成功');
  } catch (error) {
    console.error('登录时获取模型配置失败:', error);
    // 设置错误状态
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
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models: any[], forceActive = false) => {
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
      chunkSize: 800,
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
      active: forceActive || model.is_active === 1 || model.is_active === true || model.active === true,
      originalData: { ...model }
    };
    
    console.log('映射后的模型:', mappedModel);
    return mappedModel;
  });

  console.log('设置模型配置到store:', customModels);
  setAllChatSettingConfigured(customModels);
  
  // 验证设置结果
  const activeModel = customModels.find(item => item.active === true);
  if (activeModel) {
    console.log('活跃模型设置成功:', activeModel.apiModelName);
  } else {
    console.error('警告：没有找到活跃模型');
  }
};

const onFinish = async (values: any) => {
  console.log(values)
  try {
    const res = await urlRequest.login({
      username: values.values.username,
      password: values.values.password
    });
    
    if(res.code === 200) {
      Message.success('登录成功');
      Cookies.set('token', res.data.token);
      
      // 确保先设置 localStorage，再更新 store
      localStorage.setItem('userId', res.data.user_id);
      
      // 清理旧的模型配置数据，强制重新初始化
      console.log('登录成功，清理旧的模型配置');
      setAllChatSettingConfigured([]);
      
      // 先等待一下确保localStorage设置完成
      await nextTick();
      
      setUserInfo({
        userId: res.data.user_id,
        token: res.data.token,
        role: res.data.role,
        username: res.data.username
      });
      console.log('登录成功，用户信息已设置:', res.data);
      
      // 等待store更新完成 - 增加多次等待确保更新
      await nextTick();
      await nextTick();
      
      console.log('准备跳转到聊天页面，当前用户信息:', userInfo.value);
      
      // === 在登录页面直接获取模型配置，确保稳定 ===
      console.log('登录成功，立即获取模型配置...');
      
      // 设置标记，表示刚刚登录成功
      localStorage.setItem('justLoggedIn', 'true');
      
      await fetchModelConfigOnLogin(res.data);
      
      // 跳转到主页
      await router.push('/');
      
      // 跳转完成后再次等待，确保组件能读取到用户信息
      await new Promise(resolve => setTimeout(resolve, 200));
      console.log('登录流程完成，模型配置已在登录时获取');
    } else {
      Message.error(res.msg || '登录失败');
    }
  } catch (error) {
    console.error('登录失败:', error);
    Message.error('登录失败,请重试');
  }
};
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--color-fill-1);
}

.login-box {
  width: 360px;
  padding: 40px;
  background: var(--color-bg-2);
  border-radius: 20px;
  text-align: center;

  .login-icon {
    width: 48px;
    height: 48px;
    background: rgb(var(--primary-6));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
    
    :deep(.arco-icon) {
      font-size: 24px;
      color: white;
    }
  }

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: var(--color-text-1);
  }

  .subtitle {
    margin: 12px 0 32px;
    color: var(--color-text-3);
    font-size: 14px;
  }

  :deep(.arco-form) {
    .arco-form-item {
      margin-bottom: 24px;

      .arco-input-wrapper {
        background-color: var(--color-fill-2);
        border: none;
        
        &:hover, &:focus {
          background-color: var(--color-fill-3);
        }
      }

      .arco-input-prefix {
        margin-right: 8px;
        color: var(--color-text-3);
      }
    }

    .arco-btn {
      height: 44px;
      font-size: 16px;
    }
  }
}

:deep(.arco-menu-inner) {
  padding: 0 20px;
}
</style> 