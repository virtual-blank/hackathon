import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getGetMeApiV1UsersMeGetQueryKey } from '@/api/generated/👤-users/👤-users'
import {
  useGetPfpUploadUrlApiV1UsersMePfpUploadUrlPost,
  useUpdatePfpApiV1UsersMePfpPut,
} from '@/api/generated/🖼-user-profile-picture/🖼-user-profile-picture'
import { Button } from '@/shared/ui/button'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { ResponsiveModal } from '@/shared/components/ResponsiveModal'
import { AvatarCropper } from './AvatarCropper'
import { processImageFile } from '../lib/image-processing'

type AvatarUploaderProps = {
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  inputRef: React.RefObject<HTMLInputElement | null>
}

export function AvatarUploader({ onFileSelect, inputRef }: AvatarUploaderProps) {
  return (
    <input
      ref={inputRef}
      type="file"
      accept="image/png,image/jpeg,image/webp"
      className="hidden"
      onChange={onFileSelect}
    />
  )
}

type AvatarPreviewModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  file: File | null
  fileObjectUrl: string | null
  fileDimensions: { width: number; height: number } | null
}

export function AvatarPreviewModal({
  open,
  onOpenChange,
  file,
  fileObjectUrl,
  fileDimensions,
}: AvatarPreviewModalProps) {
  const queryClient = useQueryClient()
  const { mutate: getPfpUploadUrl } = useGetPfpUploadUrlApiV1UsersMePfpUploadUrlPost()
  const { mutate: updatePfp } = useUpdatePfpApiV1UsersMePfpPut()
  const [uploading, setUploading] = useState(false)
  const cropRef = useRef<{ sx: number; sy: number; size: number } | null>(null)

  const handleUpload = async () => {
    if (!file || !fileDimensions || !cropRef.current) return
    setUploading(true)

    try {
      // Process image with crop
      const blob = await processImageFile(file, cropRef.current)
      if (!blob) {
        toast.error('Не удалось обработать изображение')
        setUploading(false)
        return
      }

      const extension = blob.type === 'image/webp' ? 'webp' : 'jpeg'

      getPfpUploadUrl(
        { data: { extension } },
        {
          onSuccess: async (uploadData) => {
            try {
              const uploadRes = await fetch(uploadData.upload_url, {
                method: 'PUT',
                headers: { 'Content-Type': blob.type },
                body: blob,
              })

              if (!uploadRes.ok) {
                throw new Error('Upload failed')
              }

              updatePfp(
                { data: { file_key: uploadData.file_key } },
                {
                  onSuccess: () => {
                    queryClient.invalidateQueries({
                      queryKey: getGetMeApiV1UsersMeGetQueryKey(),
                    })
                    toast.success('Фото обновлено')
                    onOpenChange(false)
                    setUploading(false)
                  },
                  onError: () => {
                    toast.error('Не удалось загрузить фото')
                    setUploading(false)
                  },
                }
              )
            } catch {
              toast.error('Не удалось загрузить фото')
              setUploading(false)
            }
          },
          onError: () => {
            toast.error('Не удалось загрузить фото')
            setUploading(false)
          },
        }
      )
    } catch {
      toast.error('Не удалось обработать изображение')
      setUploading(false)
    }
  }

  return (
    <ResponsiveModal open={open} onOpenChange={onOpenChange} title="Новое фото">
      <div className="p-4 space-y-4 max-h-[calc(100dvh-8rem)] overflow-y-auto">
        {fileObjectUrl && fileDimensions && (
          <AvatarCropper
            src={fileObjectUrl}
            width={fileDimensions.width}
            height={fileDimensions.height}
            onChange={(crop) => {
              cropRef.current = crop
            }}
          />
        )}
        <div className="flex gap-2">
          <Button onClick={handleUpload} disabled={uploading} className="flex-1">
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Загрузка...
              </>
            ) : (
              'Сохранить'
            )}
          </Button>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={uploading}
          >
            Отмена
          </Button>
        </div>
      </div>
    </ResponsiveModal>
  )
}
