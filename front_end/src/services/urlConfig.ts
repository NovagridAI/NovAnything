/*
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-07-31 20:21:13
 * @FilePath: front_end/src/services/urlConfig.ts
 * @Description:
 */
import { useUser } from '@/store/useUser';

const { userInfo: localUserInfo } = useUser();
enum EUrlType {
  POST = 'post',
  GET = 'get',
}

enum EUrlKey {
  checkLogin = 'checkLogin',
  getLoginInfo = 'getLoginInfo',
  kbList = 'kbList',
  createKb = 'createKb',
  uploadFile = 'uploadFile',
  deleteKB = 'deleteKB',
  deleteFile = 'deleteFile',
  uploadUrl = 'uploadUrl',
  kbConfig = 'kbConfig',
  fileList = 'fileList',
  createBot = 'createBot',
  updateBot = 'updateBot',
  queryBotInfo = 'queryBotInfo',
  deleteBot = 'deleteBot',
  uploadFaqs = 'uploadFaqs',
  getFile = 'getFile',
  getDocCompleted = 'getDocCompleted',
  updateDocCompleted = 'updateDocCompleted',
  clearUpload = 'clearUpload',
  sendQuestion = 'sendQuestion',
  getQAInfo = 'getQAInfo',
  getKbInfo = 'getKbInfo',
  getTags = 'getTags',
  updateTags = 'updateTags',
  login = 'login',
  userList = 'userList',
  departmentList = 'departmentList',
  createDepartment = 'createDepartment',
  groupList = 'groupList',
  createUser = 'createUser',
  deleteUser = 'deleteUser',
  updateDepartment = 'updateDepartment',
  deleteDepartment = 'deleteDepartment',
  updateUser = 'updateUser',
  createGroup = 'createGroup',
  deleteGroup = 'deleteGroup',
  grantKbAccess = 'grantKbAccess',
  revokeKbAccess = 'revokeKbAccess',
  addUserToGroup = 'addUserToGroup',
  removeUserFromGroup = 'removeUserFromGroup',
  updateUserRole = 'updateUserRole',
}

interface IUrlValueConfig {
  type: EUrlType;
  url: string;
  showLoading?: boolean;
  loadingId?: string;
  // errorToast?: boolean;//默认开启
  cancelRepeat?: boolean;
  sign?: boolean; // 是否开启签名
  param?: any;

  [key: string]: any;
}

type IUrlConfig = Record<EUrlKey, IUrlValueConfig>;

import services from '.';

export const userId = localUserInfo.userId;

const userIdD = () => localUserInfo.userId
export const userPhone = localUserInfo.phoneNumber;

//ajax请求接口
const urlConfig: IUrlConfig = {
  checkLogin: {
    type: EUrlType.GET,
    url: '/checkLogin.s',
  },
  login: {
    type: EUrlType.POST,
    url: '/auth/login',
    showLoading: true,
    param: {
      username: '',
      password: ''
    }
  },
  getLoginInfo: {
    type: EUrlType.POST,
    url: '/j_spring_security_check',
  },
  // 获取知识库列表
  kbList: {
    type: EUrlType.POST,
    url: '/user/list_knowledge_base',
    showLoading: true,
    param: {
      user_id: userIdD(),
      user_info: userPhone,
    },
  },
  // 新建知识库
  createKb: {
    type: EUrlType.POST,
    url: '/local_doc_qa/new_knowledge_base',
    showLoading: true,
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 上传文件
  uploadFile: {
    type: EUrlType.POST,
    url: '/local_doc_qa/upload_files',
    param: {
      user_id: userId,
      // user_info: userPhone,
    },
  },
  // 删除知识库
  deleteKB: {
    type: EUrlType.POST,
    url: '/local_doc_qa/delete_knowledge_base',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 删除文件
  deleteFile: {
    type: EUrlType.POST,
    url: '/local_doc_qa/delete_files',
    showLoading: true,
    param: {
      user_id: userId,
      user_info: userPhone,
      kb_id: '',
      file_ids: [],
    },
  },
  // 上传网页文件
  uploadUrl: {
    type: EUrlType.POST,
    url: '/local_doc_qa/upload_weblink',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  kbConfig: {
    type: EUrlType.POST,
    url: '/local_doc_qa/rename_knowledge_base',
    showLoading: true,
    param: {
      user_id: userId,
      user_info: userPhone,
      kb_id: '',
      new_kb_name: '',
    },
  },
  //获取知识库已上传文件状态
  fileList: {
    type: EUrlType.POST,
    url: '/local_doc_qa/list_files',
    param: {
      user_id: userId,
      user_info: userPhone,
      kb_id: '',
    },
  },
  // 创建Bot
  createBot: {
    type: EUrlType.POST,
    url: '/local_doc_qa/new_bot',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 更新Bot
  updateBot: {
    type: EUrlType.POST,
    url: '/local_doc_qa/update_bot',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 获取Bot信息/列表
  queryBotInfo: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_bot_info',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  //删除Bot
  deleteBot: {
    type: EUrlType.POST,
    url: '/local_doc_qa/delete_bot',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  //上传faq
  uploadFaqs: {
    type: EUrlType.POST,
    url: '/local_doc_qa/upload_faqs',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  //获取文件base64
  getFile: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_file_base64',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 获取文档解析内容（chunk）
  getDocCompleted: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_doc_completed',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 修改文档解析内容（chunk）
  updateDocCompleted: {
    type: EUrlType.POST,
    url: '/local_doc_qa/update_chunks',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 取消知识库所有文件上传
  clearUpload: {
    type: EUrlType.POST,
    url: '/local_doc_qa/clean_files_by_status',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 发送问题，非流式需要用这个
  sendQuestion: {
    type: EUrlType.POST,
    url: '/local_doc_qa/local_doc_chat',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 检索qa日志
  getQAInfo: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_qa_info',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 获取所有知识库状态
  getKbInfo: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_total_status',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 获取标签, 通过kbids
  getTags: {
    type: EUrlType.POST,
    url: '/local_doc_qa/get_tags',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 更新标签
  updateTags: {
    type: EUrlType.POST,
    url: '/local_doc_qa/update_tags',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  // 获取用户列表
  userList: {
    type: EUrlType.GET,
    url: '/user/list',
    showLoading: false,
    param: {
      user_id: userId,
    }
  },
  // 获取部门列表
  departmentList: {
    type: EUrlType.GET,
    url: '/department/list',
    showLoading: false,
    param: {
      user_id: userId,
    }
  },
  // 创建部门
  createDepartment: {
    type: EUrlType.POST,
    url: '/department/create',
    showLoading: false,
    param: {
      name: '',
      description: '',
      parent_id: ''
    }
  },
  groupList: {
    type: EUrlType.GET,
    url: '/group/list',
    showLoading: false,
    param: {
      user_id: userId
    }
  },
  createUser: {
    type: EUrlType.POST,
    url: '/user/create',
    param: {
      user_id: userId,
      user_info: userPhone,
    },
  },
  deleteUser: {
    type: EUrlType.POST,
    url: '/user/delete',
    param: {
      user_id: userId,
    },
  },
  // 更新部门
  updateDepartment: {
    type: EUrlType.POST,
    url: '/department/update',
    showLoading: false,
    param: {
      dept_id: '',
      parent_dept_id: '',
      user_id: userId
    }
  },
  // 删除部门
  deleteDepartment: {
    type: EUrlType.POST,
    url: '/department/delete',
    showLoading: false,
    param: {
      dept_id: '',
      user_id: userId
    }
  },
  // 更新用户信息（包括部门）
  updateUser: {
    type: EUrlType.POST,
    url: '/user/update',
    showLoading: false,
    param: {
      user_id: '',
      dept_id: null
    }
  },
  // 创建群组
  createGroup: {
    type: EUrlType.POST,
    url: '/group/create',
    showLoading: false,
    param: {
      name: '',
      description: '',
      user_id: userId
    }
  },
  // 删除群组
  deleteGroup: {
    type: EUrlType.POST,
    url: '/group/delete',
    showLoading: false,
    param: {
      group_id: '',
      user_id: userId
    }
  },
  // 授予知识库访问权限
  grantKbAccess: {
    type: EUrlType.POST,
    url: '/kb/grant_access',
    showLoading: true,
    param: {
      kb_id: '',
      user_id: userId,
      subject_type: '',
      subject_id: '',
      permission_type: ''
    }
  },
  // 撤销知识库访问权限
  revokeKbAccess: {
    type: EUrlType.POST,
    url: '/kb/revoke_access',
    showLoading: true,
    param: {
      kb_id: '',
      user_id: userId,
      subject_type: '',
      subject_id: ''
    }
  },
  // 添加用户到群组
  addUserToGroup: {
    type: EUrlType.POST,
    url: '/group/add_user',
    showLoading: false,
    param: {
      user_id: userId,
      target_user_id: '',
      group_id: ''
    }
  },

  // 从群组移除用户
  removeUserFromGroup: {
    type: EUrlType.POST,
    url: '/group/remove_user',
    showLoading: false,
    param: {
      user_id: userId,
      target_user_id: '',
      group_id: ''
    }
  },

  // 更新用户角色
  updateUserRole: {
    type: EUrlType.POST,
    url: '/user/update',
    showLoading: true,
    param: {
      user_id: userId,
      target_user_id: '',
      role: ''
    }
  }
};

// 使用映射类型来创建一个类型，该类型将urlConfig中的每个键映射到IRequestMethod类型
type UrlRequestMethods = {
  [K in keyof typeof urlConfig]: any;
};

const urlResquest: UrlRequestMethods = {} as UrlRequestMethods;
Object.keys(urlConfig).forEach(key => {
  urlResquest[key] = (params: any, option: any = {}) => {
    const { type, url, param, ...other } = urlConfig[key];
    return services[type](url, { ...param, ...params }, { ...other, ...option });
  };
});
export default urlResquest;
