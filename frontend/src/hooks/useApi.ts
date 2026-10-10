import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import {
  Email,
  EmailList,
  EmailAddress,
  EmailAddressList,
  GenerateEmailResponse,
  LoginResponse,
  StatsResponse,
  HealthResponse,
  OTPCode,
  VerificationLink,
} from '@/types'

export const useGenerateEmail = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { count?: number; domain?: string; ttl_hours?: number; prefix?: string; password_protected?: boolean; max_emails?: number }) =>
      apiClient.post<GenerateEmailResponse>('/addresses/generate', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-addresses'] })
    },
  })
}

export const useCreateCustomEmail = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { local_part: string; domain: string; password?: string; max_emails?: number }) =>
      apiClient.post<EmailAddress>(`/addresses`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-addresses'] })
    },
  })
}

export const useLogin = () => {
  return useMutation({
    mutationFn: (data: { email: string; password?: string }) =>
      apiClient.post<LoginResponse>('/auth/login', data),
  })
}

export const useEmailAddresses = (page = 1, perPage = 20, status?: string) => {
  return useQuery({
    queryKey: ['email-addresses', page, perPage, status],
    queryFn: () =>
      apiClient.get<EmailAddressList>('/addresses', { page, per_page: perPage, status }),
  })
}

export const useEmailAddress = (id: string) => {
  return useQuery({
    queryKey: ['email-address', id],
    queryFn: () => apiClient.get<EmailAddress>(`/addresses/${id}`),
    enabled: !!id,
  })
}

export const useDeleteEmailAddress = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/addresses/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-addresses'] })
    },
  })
}

export const useExtendEmailAddress = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, hours }: { id: string; hours: number }) =>
      apiClient.post<EmailAddress>(`/addresses/${id}/extend?ttl_hours=${hours}`, null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['email-address', variables.id] })
    },
  })
}

export const useInbox = (
  emailId: string,
  page = 1,
  pageSize = 20,
  status?: string,
  search?: string,
  options?: Partial<UseQueryOptions<EmailList>>
) => {
  return useQuery({
    queryKey: ['inbox', emailId, page, pageSize, status, search],
    queryFn: () =>
      apiClient.get<EmailList>(`/emails/${emailId}/inbox`, {
        page,
        page_size: pageSize,
        status,
        search,
      }),
    refetchInterval: 2000,
    refetchIntervalInBackground: true,
    ...options,
  })
}

export const useEmail = (emailId: string, messageId: string) => {
  return useQuery({
    queryKey: ['email', emailId, messageId],
    queryFn: () => apiClient.get<Email>(`/emails/${emailId}/emails/${messageId}`),
    enabled: !!messageId,
  })
}

export const useEmailDetail = (emailId: string, messageId: string) => {
  return useQuery({
    queryKey: ['email-detail', emailId, messageId],
    queryFn: () => apiClient.get<any>(`/emails/${emailId}/emails/${messageId}`),
    enabled: !!messageId,
  })
}

export const useDeleteEmail = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ emailId, messageId }: { emailId: string; messageId: string }) =>
      apiClient.delete(`/emails/${emailId}/emails/${messageId}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inbox', variables.emailId] })
    },
  })
}

export const useDeleteAllEmails = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (emailId: string) => apiClient.delete(`/emails/${emailId}/emails`),
    onSuccess: (_, emailId) => {
      queryClient.invalidateQueries({ queryKey: ['inbox', emailId] })
    },
  })
}

export const useMarkAsRead = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ emailId, messageId }: { emailId: string; messageId: string }) =>
      apiClient.post(`/emails/${emailId}/emails/${messageId}/read`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inbox', variables.emailId] })
    },
  })
}

export const useExtractOTP = (emailId: string, messageId: string) => {
  return useQuery({
    queryKey: ['otp', emailId, messageId],
    queryFn: () =>
      apiClient.get<{ otp_codes: OTPCode[]; verification_links: VerificationLink[] }>(
        `/emails/${emailId}/emails/${messageId}/otp`
      ),
    enabled: !!messageId,
  })
}

export const useEmailStats = (emailId: string) => {
  return useQuery({
    queryKey: ['email-stats', emailId],
    queryFn: () => apiClient.get<StatsResponse>(`/addresses/${emailId}/stats`),
    refetchInterval: 5000,
  })
}

export const useDomains = () => {
  return useQuery({
    queryKey: ['domains'],
    queryFn: () => apiClient.get<{ domain: string; is_default: boolean; emails_received: number }[]>('/addresses/domains'),
  })
}

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.get<HealthResponse>('/health/detailed'),
    refetchInterval: 30000,
  })
}

export const useTimer = (emailId: string) => {
  return useQuery({
    queryKey: ['timer', emailId],
    queryFn: () => apiClient.get<{ expired: boolean; expires_at: string; seconds_remaining: number; formatted: string }>(`/emails/${emailId}/timer`),
    refetchInterval: 1000,
  })
}