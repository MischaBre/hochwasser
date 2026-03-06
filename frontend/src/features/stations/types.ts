export type StationSummary = {
  uuid: string
  number: string
  shortname: string
  longname: string
  km: number | null
  agency: string
  longitude: number | null
  latitude: number | null
  water_shortname: string
  water_longname: string
}

export type StationListResponse = {
  items: StationSummary[]
  limit: number
  offset: number
}

export type ListStationsParams = {
  search?: string
  limit?: number
  offset?: number
  uuids?: string[]
}

export type StationMeasurement = {
  timestamp: string
  value: number
}
