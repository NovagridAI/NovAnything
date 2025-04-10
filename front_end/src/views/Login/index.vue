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
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useUser } from '@/store/useUser';
import { IconEmail, IconLock } from '@arco-design/web-vue/es/icon';
import { Message } from '@arco-design/web-vue';
import urlRequest from '@/services/urlConfig';
import Cookies from 'js-cookie';

const router = useRouter();
const { setUserInfo } = useUser();
const formState = reactive({
  username: '',
  password: ''
});

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
      setUserInfo({
        userId: res.data.user_id,
        token: res.data.token,
        role: res.data.role,
        username: res.data.username
      });
      console.log(res.data, res.data.user_id)
      await nextTick();
      await router.push('/');
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