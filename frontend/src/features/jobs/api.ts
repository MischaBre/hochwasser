import { apiRequest } from '@/api/client'
import type { Job, JobCreatePayload, JobStatus, JobUpdatePayload, OutboxListResponse } from '@/features/jobs/types'

export const listJobs = (includeDisabled = false) => apiRequest<Job[]>(`/v1/jobs?include_disabled=${includeDisabled}`)

export const createJob = (payload: JobCreatePayload) => apiRequest<Job>('/v1/jobs', { method: 'POST', body: payload })

export const updateJob = (jobUuid: string, payload: JobUpdatePayload) =>
  apiRequest<Job>(`/v1/jobs/${encodeURIComponent(jobUuid)}`, { method: 'PATCH', body: payload })

export const deleteJob = (jobUuid: string) => apiRequest<void>(`/v1/jobs/${encodeURIComponent(jobUuid)}`, { method: 'DELETE' })

export const getJobStatus = (jobUuid: string) => apiRequest<JobStatus>(`/v1/jobs/${encodeURIComponent(jobUuid)}/status`)

export const getJobOutbox = (jobUuid: string, limit: number, offset: number) =>
  apiRequest<OutboxListResponse>(`/v1/jobs/${encodeURIComponent(jobUuid)}/outbox?limit=${limit}&offset=${offset}`)
