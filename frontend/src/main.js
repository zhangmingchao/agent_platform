// 前端应用的启动入口：在这里创建 Vue 应用并安装全局能力。
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// App 是根组件；router、i18n 与全局样式会作用于整个应用。
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './styles/global.css'

// 引入 Element Plus 语言包
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

// 创建 Vue 应用实例，后续 app.use() 都是在给该实例安装插件。
const app = createApp(App)

// Element Plus 图标以组件形式注册后，任意页面都可直接使用 <Plus />、<Robot /> 等。
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia()) // 注册 Pinia：提供全局状态管理能力。
app.use(router) // 注册 Vue Router：根据 URL 切换页面组件。
app.use(i18n) // 注册国际化：页面中可使用 t('xxx') 获取文案。

// Element Plus 自身也有内置文案（如分页、日期选择器），需要单独指定语言包。
const localeMap = {
  'zh-CN': zhCn,
  'en-US': en
}
app.use(ElementPlus, {
  locale: localeMap[i18n.global.locale.value] || zhCn
})

// 将整个 Vue 应用挂载到 index.html 中的 <div id="app">。
app.mount('#app')
