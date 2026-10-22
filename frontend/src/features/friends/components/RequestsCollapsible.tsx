import { useState } from 'react'
import { UserPlus, ChevronDown } from 'lucide-react'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/lib/utils'
import { RequestRow } from './RequestRow'
import type { FriendSchema } from '@/api/generated/model'

type RequestsCollapsibleProps = {
  incoming: FriendSchema[]
  outgoing: FriendSchema[]
}

export function RequestsCollapsible({
  incoming,
  outgoing,
}: RequestsCollapsibleProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [tab, setTab] = useState<'incoming' | 'outgoing'>('incoming')

  const currentList = tab === 'incoming' ? incoming : outgoing

  return (
    <div className="bg-surface-elevated rounded-2xl shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls="requests-content"
        className="w-full px-4 py-4 flex items-start gap-3 text-left rounded-2xl hover:bg-muted/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <UserPlus className="h-5 w-5 text-foreground mt-0.5 shrink-0" strokeWidth={1.75} />
        <div className="flex-1 min-w-0">
          <p className="text-[15px] font-semibold text-foreground">
            Заявки в друзья
          </p>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Всего заявок: {incoming.length}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {incoming.length > 0 && (
            <Badge variant="default" className="h-5 px-2 text-xs">
              {incoming.length}
            </Badge>
          )}
          <ChevronDown
            className={cn(
              'h-4 w-4 text-muted-foreground transition-transform duration-200',
              isOpen && 'rotate-180'
            )}
            strokeWidth={1.75}
          />
        </div>
      </button>

      <div
        id="requests-content"
        className={cn(
          'grid transition-[grid-template-rows] duration-200',
          isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        )}
        style={{ transitionProperty: 'grid-template-rows' }}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="flex flex-col px-4 pb-4">
            {/* Radio pills */}
            <div className="flex gap-2 p-1 bg-muted rounded-full shrink-0">
              <label className={cn(
                'flex-1 flex items-center justify-center gap-2 h-8 rounded-full px-3 cursor-pointer transition-all',
                tab === 'incoming' && 'bg-surface-elevated shadow-sm'
              )}>
                <input
                  type="radio"
                  name="requests-tab"
                  value="incoming"
                  checked={tab === 'incoming'}
                  onChange={() => setTab('incoming')}
                  className="sr-only"
                />
                <span className="text-sm font-medium">Входящие</span>
                {incoming.length > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {incoming.length}
                  </span>
                )}
              </label>
              <label className={cn(
                'flex-1 flex items-center justify-center gap-2 h-8 rounded-full px-3 cursor-pointer transition-all',
                tab === 'outgoing' && 'bg-surface-elevated shadow-sm'
              )}>
                <input
                  type="radio"
                  name="requests-tab"
                  value="outgoing"
                  checked={tab === 'outgoing'}
                  onChange={() => setTab('outgoing')}
                  className="sr-only"
                />
                <span className="text-sm font-medium">Отправленные</span>
                {outgoing.length > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {outgoing.length}
                  </span>
                )}
              </label>
            </div>

            {/* List */}
            <div className="mt-3 max-h-[360px] overflow-y-auto overflow-x-hidden overscroll-contain pr-1 space-y-1">
              {currentList.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  {tab === 'incoming'
                    ? 'Входящих заявок нет'
                    : 'Отправленных заявок нет'}
                </p>
              ) : (
                currentList.map((request) => (
                  <RequestRow key={request.id} request={request} type={tab} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
