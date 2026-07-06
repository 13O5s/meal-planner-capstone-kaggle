export const card = {
  wrapper: 'overflow-hidden rounded-[20px] border-zinc-800/50',
  header: 'px-8 pt-8 pb-0',
  content: 'px-8 pt-6 pb-8 space-y-6',
}

export const typography = {
  h1: 'text-2xl font-bold tracking-tight',
  subtitle: 'text-zinc-400 mt-1.5 text-sm',
  sectionTitle: 'text-base font-semibold tracking-tight',
  sectionHeader: 'flex items-center gap-2.5',
}

export const icon = {
  section: 'w-5 h-5 text-emerald-500',
  pill: 'w-4 h-4',
}

export const pill = {
  base: 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950',
  active: 'bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-lg scale-[1.02] border-0',
  inactive: 'bg-transparent border border-zinc-700 text-zinc-300 hover:bg-zinc-800/50 hover:border-zinc-500',
}

export const button = {
  primary: 'inline-flex items-center gap-2.5 px-7 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 text-white font-medium text-sm shadow-md hover:shadow-lg hover:-translate-y-0.5 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-md transition-all duration-200 min-h-[48px]',
  secondary: 'inline-flex items-center gap-2.5 px-7 py-3 rounded-xl bg-transparent border border-zinc-700 text-zinc-300 font-medium text-sm hover:bg-zinc-800/50 hover:border-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 min-h-[48px]',
}

export const input = {
  base: 'w-full px-4 py-2.5 rounded-xl bg-zinc-900 border border-zinc-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200',
  date: 'w-full pl-12 pr-4 py-2.5 rounded-xl bg-zinc-900 border border-zinc-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200',
}

export const divider = {
  vertical: 'w-px self-stretch bg-zinc-700',
  horizontal: 'w-full h-px bg-zinc-700',
}
