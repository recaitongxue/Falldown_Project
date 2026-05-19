import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/test',
    name: 'TestPage',
    component: () => import('../views/TestPage.vue')
  },
  
  // 用户端路由
  {
    path: '/user',
    name: 'UserLayout',
    component: () => import('../layout/UserLayout.vue'),
    children: [
      {
        path: '',
        name: 'UserDashboard',
        component: () => import('../views/user/UserDashboard.vue')
      },
      {
        path: 'upload',
        name: 'UserUpload',
        component: () => import('../views/user/UserUpload.vue')
      },
      {
        path: 'history',
        name: 'UserHistory',
        component: () => import('../views/user/UserHistory.vue')
      },
      {
        path: 'alerts',
        name: 'UserAlerts',
        component: () => import('../views/user/UserAlerts.vue')
      },
      {
        path: 'ai-assistant',
        name: 'UserAIAssistant',
        component: () => import('../views/user/UserAIAssistant.vue')
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('../views/user/UserProfile.vue')
      },
      {
        path: 'camera',
        name: 'UserCamera',
        component: () => import('../views/user/UserCamera.vue')
      },
      {
        path: 'cameras',
        name: 'UserCameraManage',
        component: () => import('../views/user/UserCameraManage.vue')
      }
    ]
  },
  
  // 管理员端路由
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('../layout/AdminLayout.vue'),
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/AdminDashboard.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/admin/AdminUsers.vue')
      },
      {
        path: 'statistics',
        name: 'AdminStatistics',
        component: () => import('../views/admin/AdminStatistics.vue')
      },
      {
        path: 'alerts',
        name: 'AdminAlerts',
        component: () => import('../views/admin/AdminAlerts.vue')
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('../views/admin/AdminSettings.vue')
      },
      {
        path: 'cameras',
        name: 'AdminCameras',
        component: () => import('../views/admin/AdminCameras.vue')
      },
      {
        path: 'ai-assistant',
        name: 'AdminAIAssistant',
        component: () => import('../views/admin/AdminAIAssistant.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const user = sessionStorage.getItem('user') ? JSON.parse(sessionStorage.getItem('user')) : null
  
  // 测试页面不需要登录
  if (to.path === '/test') {
    next()
    return
  }
  
  // 登录页面不需要登录
  if (to.path === '/login') {
    next()
    return
  }
  
  // 需要登录的页面
  if (!user) {
    next('/login')
    return
  }
  
  // 权限校验
  const isAdmin = user.role === 'admin'
  const isAdminRoute = to.path.startsWith('/admin')
  const isUserRoute = to.path.startsWith('/user')
  
  // 管理员访问管理员路由
  if (isAdminRoute && isAdmin) {
    next()
    return
  }
  
  // 用户访问用户路由
  if (isUserRoute && !isAdmin) {
    next()
    return
  }
  
  // 重定向到对应角色的首页
  const redirectPath = isAdmin ? '/admin' : '/user'
  if (to.path !== redirectPath) {
    next(redirectPath)
  } else {
    next()
  }
})

export default router
