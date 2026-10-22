type ApiError = {
  detail?: string | Array<{ loc: string[]; msg: string; type: string }>
}

/**
 * Maps API error responses to user-friendly Russian messages
 */
export function getErrorMessage(error: unknown): string {
  if (!error) {
    return 'Произошла неизвестная ошибка'
  }

  // Handle API error structure
  if (typeof error === 'object' && 'detail' in error) {
    const apiError = error as ApiError
    const { detail } = apiError

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail) && detail.length > 0) {
      // Return first validation error message
      return detail[0].msg
    }
  }

  // Handle Error instances
  if (error instanceof Error) {
    return error.message
  }

  return 'Произошла неизвестная ошибка'
}
