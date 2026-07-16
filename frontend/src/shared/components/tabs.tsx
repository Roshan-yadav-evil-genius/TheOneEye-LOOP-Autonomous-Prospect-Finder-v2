import * as RadixTabs from '@radix-ui/react-tabs'
import type { ReactNode } from 'react'

export interface TabItem {
  content: ReactNode
  label: string
  value: string
}

interface TabsProps {
  defaultValue?: string
  items: TabItem[]
  label?: string
  onValueChange?: (value: string) => void
  value?: string
}

export function Tabs({ defaultValue, items, label = 'Page sections', onValueChange, value }: TabsProps) {
  return (
    <RadixTabs.Root
      className="tabs"
      defaultValue={defaultValue}
      onValueChange={onValueChange}
      value={value}
    >
      <RadixTabs.List className="tabs__list" aria-label={label}>
        {items.map((item) => (
          <RadixTabs.Trigger className="tabs__trigger" key={item.value} value={item.value}>
            {item.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {items.map((item) => (
        <RadixTabs.Content className="tabs__content" key={item.value} value={item.value}>
          {item.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  )
}
