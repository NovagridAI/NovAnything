/*
 * @Author: 祝占朋 wb.zhuzp01@rd.netease.com
 * @Date: 2023-11-09 17:37:50
 * @LastEditors: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @LastEditTime: 2024-01-11 10:41:49
 * @FilePath: /QAnything/front_end/src/router/index.ts
 * @Description:
 */
import { createRouter, createWebHashHistory } from 'vue-router';
import { routes } from './routes';
// import { useUser } from '@/store/useUser';
// 导入进度条
import { start, close } from '@/utils/nporgress';
import { checkVersion } from '@/utils/version';
import Cookies from 'js-cookie';

//是否隐藏NavBar

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});
router.beforeEach((to, from, next) => {
  start();
  checkVersion();
  next();
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = Cookies.get('token'); // 判断是否已登录

  if (to.path !== '/login' && !isAuthenticated) {
    next('/login');
  } else {
    next();
  }
});

router.afterEach(() => {
  close();
});
export default router;
