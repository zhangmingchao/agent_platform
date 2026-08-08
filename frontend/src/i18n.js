// 国际化初始化：集中注册所有语言包，并确定当前使用的语言。
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

// 优先使用用户之前选择的语言；没有时按浏览器语言决定默认值。
const savedLocale = localStorage.getItem('locale')
const browserLocale = navigator.language === 'en-US' ? 'en-US' : 'zh-CN'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: savedLocale || browserLocale,
  // 某个 key 没有翻译时，回退到中文，避免页面出现空白。
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export default i18n
