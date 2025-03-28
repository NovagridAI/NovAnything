/*
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @LastEditTime: 2024-01-11 10:47:54
 * @FilePath: /QAnything/front_end/src/main.ts
 * @Description:
 */

import { createApp } from 'vue';
import App from './App.vue';
import router from './router/index';
import pinia from './store/index';
import '@/styles/common/global.scss';
import 'virtual:svg-icons-register';
import ArcoVue from '@arco-design/web-vue';
import SvgIcon from '@/components/SvgIcon.vue';
import '@arco-design/web-vue/dist/arco.css';

const vueApp = createApp(App);

vueApp.use(ArcoVue, {
    // 用于改变使用组件时的前缀名称
    componentPrefix: 'arco'
});

vueApp.use(pinia).use(router);
vueApp.component('SvgIcon', SvgIcon);
vueApp.mount('#app');
