import { cn } from '@/utils/cn'

interface SkeletonProps {
  className?: string
  width?: string | number
  height?: string | number
  rounded?: boolean
}

export const Skeleton = ({ className, width, height, rounded }: SkeletonProps) => (
  <div
    className={cn('skeleton', rounded && 'rounded-full', className)}
    style={{ width, height }}
  />
)

export const SkeletonText = ({ lines = 3 }: { lines?: number }) => (
  <div className="flex flex-col gap-2">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} className="h-4" width={`${90 - i * 10}%`} />
    ))}
  </div>
)

export const SkeletonCard = () => (
  <div className="flex flex-col gap-3">
    <Skeleton className="h-8" width="60%" />
    <Skeleton className="h-4" width="40%" />
    <SkeletonText lines={2} />
  </div>
)

export const SkeletonEmail = () => (
  <div className="flex items-center gap-4 p-4 rounded-xl">
    <Skeleton rounded width={40} height={40} />
    <div className="flex-1 flex flex-col gap-2">
      <Skeleton className="h-4" width="50%" />
      <Skeleton className="h-3" width="80%" />
      <Skeleton className="h-3" width="30%" />
    </div>
  </div>
)