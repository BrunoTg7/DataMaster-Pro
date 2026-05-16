type Theme = 'light' | 'dark' | 'system'

export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ')
}

export function getThemeClass(theme: Theme, lightClass: string, darkClass: string): string {
  if (theme === 'system') {
    return cn(lightClass, 'dark:' + darkClass.split(' ').join('-dark:'))
  }
  return theme === 'dark' ? darkClass : lightClass
}

export function getBgClass(theme: Theme): string {
  return getThemeClass(theme, 'bg-white', 'bg-surface-900')
}

export function getBgSecondaryClass(theme: Theme): string {
  return getThemeClass(theme, 'bg-surface-50', 'bg-surface-800')
}

export function getTextClass(theme: Theme): string {
  return getThemeClass(theme, 'text-surface-900', 'text-surface-50')
}

export function getTextSecondaryClass(theme: Theme): string {
  return getThemeClass(theme, 'text-surface-600', 'text-surface-400')
}

export function getBorderClass(theme: Theme): string {
  return getThemeClass(theme, 'border-surface-200', 'border-surface-800')
}