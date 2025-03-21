/*
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-02 16:02:06
 * @FilePath: front_end/src/store/useKnowledgeBase.ts
 * @Description:
 */

import { IKnowledgeItem } from '@/utils/types';
import { pageStatus } from '@/utils/enum';
// import { resultControl } from '@/utils/utils';
import message from 'ant-design-vue/es/message';

import urlResquest from '@/services/urlConfig';
import { getLanguage } from '@/language/index';

const common = getLanguage().common;

export const useKnowledgeBase = defineStore(
  'knowledgeBase',
  () => {
    // 当前操作的知识库id
    const currentId = ref('');
    const setCurrentId = (id: string) => {
      currentId.value = id;
    };

    watch(
      () => currentId.value,
      () => {
        console.log('current', currentId.value);
      }
    );

    //选中的知识库id
    const selectList = ref<string[]>([]);
    const setSelectList = list => {
      selectList.value = list;
    };

    // 当前操作的知识库名字
    const currentKbName = ref('');
    const setCurrentKbName = (id: string) => {
      currentKbName.value = id;
    };

    //获取到的知识库列表
    const knowledgeBaseList = ref<Array<IKnowledgeItem>>([]);
    const setKnowledgeBaseList = list => {
      knowledgeBaseList.value = list;
    };

    //需要判断是否有知识库 如果没有知识库 展示default内容
    const showDefault = ref(pageStatus.initing);
    const setDefault = str => {
      showDefault.value = str;
    };

    //是否展示删除弹窗
    const showDeleteModal = ref(false);
    const setShowDeleteModal = (flag: boolean) => {
      showDeleteModal.value = flag;
    };

    //获取知识库列表
    const getList = async () => {
      try {
        const res: any = await urlResquest.kbList();
        if (+res.code === 200) {
          if (res?.data?.length > 0) {
            // const list = res.data.filter(item => !/.*_FAQ$/.test(item.kb_name));
            const list = res.data;
            setKnowledgeBaseList(list);
            setDefault(pageStatus.normal);

            if (!selectList.value.length) {
              selectList.value.push(list[0]?.kb_id);
            }
          } else {
            setKnowledgeBaseList([]);
            setDefault(pageStatus.default);
          }
        } else if (+res.code === 500) {
          setKnowledgeBaseList([]);
          setDefault(pageStatus.default);
          message.error(res.msg || common.error);
        }
      } catch (e) {
        setKnowledgeBaseList([]);
        setDefault(pageStatus.default);
        message.error(e.msg || common.error);
      }
    };

    return {
      currentId,
      setCurrentId,
      knowledgeBaseList,
      setKnowledgeBaseList,
      showDeleteModal,
      setShowDeleteModal,
      showDefault,
      setDefault,
      getList,
      currentKbName,
      setCurrentKbName,
      selectList,
      setSelectList,
    };
  },
  {
    persist: {
      storage: localStorage,
    },
  }
);
