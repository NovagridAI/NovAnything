/*
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @LastEditTime: 2024-01-11 10:45:47
 * @FilePath: /QAnything/front_end/src/store/useUser.ts
 * @Description:
 */

export const useUser = defineStore(
  'user',
  () => {
    const userInfo: any = ref({
      token: '',
      phoneNumber: '1',
      userId: '',
      role: ''
    });

    const userPhoneDialogOpen = ref(false);

    const setUserInfo = info => {
      userInfo.value.token = info.token;
      userInfo.value.userId = info.userId;
      userInfo.value.role = info.role;
    };

    const getCachePhone = () => {
      return userInfo.value.phoneNumber;
    };

    const setPhoneNumber = phone => {
      userInfo.value.phoneNumber = phone;
    };

    const checkPhone = () => {
      const cachePhone = getCachePhone();
      if (cachePhone.trim() === '1') {
        userPhoneDialogOpen.value = true;
        return false;
      }
      return true;
    };

    return {
      userInfo,
      setUserInfo,
      setPhoneNumber,
      userPhoneDialogOpen,
      checkPhone,
    };
  },
  {
    persist: {
      storage: localStorage,
    },
  }
);
