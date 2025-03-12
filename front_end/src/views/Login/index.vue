<template>
  <div class="login-container">
    <div class="login-box">
      <!-- 登录图标 -->
      <div class="login-icon">
        <LockOutlined />
      </div>
      
      <h2>登录</h2>
      <p class="subtitle">输入邮箱和密码登录</p>

      <a-form
        :model="formState"
        name="basic"
        :wrapper-col="{ span: 24 }"
        autocomplete="off"
        @finish="onFinish"
      >
        <a-form-item
          name="username"
          :rules="[{ required: true, message: '请输入邮箱' }]"
        >
          <a-input 
            style="padding: 10px;"
            v-model:value="formState.username" 
            placeholder="Email"
            size="large"
          >
            <template #prefix >
              <MailOutlined style="margin-right: 10px; margin-left: 5px;" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password 
            style="padding: 10px;"
            v-model:value="formState.password" 
            placeholder="Password"
            size="large"
          >
            <template #prefix>
              <LockOutlined style="margin-right: 10px; margin-left: 5px;" />
            </template>
          </a-input-password>
        </a-form-item>

        <!-- <div class="forgot-password">
          <a href="#">Forgot password?</a>
        </div> -->

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" style="width: 100%; height: 48px;">登录</a-button>
        </a-form-item>

        <!-- <div class="signup-link">
          Don't have an account? <a href="#">Sign up</a>
        </div> -->
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useUser } from '@/store/useUser';
import { MailOutlined, LockOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import urlRequest from '@/services/urlConfig';
import Cookies from 'js-cookie';

const router = useRouter();
const { setUserInfo } = useUser();
const formState = reactive({
  username: '',
  password: ''
});

const onFinish = async (values: any) => {
  try {
    const res = await urlRequest.login({
      username: values.username,
      password: values.password
    });
    
    if(res.code === 200) {
      message.success('登录成功');
      Cookies.set('token', res.data.access_token);
      setUserInfo({
        userId: res.data.user_id,
        token: res.data.access_token
      });
      localStorage.setItem('userId', res.data.user_id);
      await router.push('/');
      console.log('路由跳转完成');
    } else {
      message.error(res.msg || '登录失败');
    }
  } catch (error) {
    console.error('登录失败:', error);
    message.error('登录失败,请重试');
  }
};
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fb;
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  text-align: center;

  .login-icon {
    width: 48px;
    height: 48px;
    background: #007bff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
    
    :deep(.anticon) {
      font-size: 24px;
      color: white;
    }
  }

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: #1a1f36;
  }

  .subtitle {
    margin: 12px 0 32px;
    color: #6b7280;
    font-size: 14px;
  }

  .forgot-password {
    text-align: right;
    margin: -8px 0 16px;
    
    a {
      color: #007bff;
      font-size: 14px;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }

  .signup-link {
    margin-top: 24px;
    color: #6b7280;
    font-size: 14px;

    a {
      color: #007bff;
      text-decoration: none;
      font-weight: 500;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}
</style> 