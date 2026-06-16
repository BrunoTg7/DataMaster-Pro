import { describe, it, expect } from 'vitest'
import { APP_VERSION, PLAN_LIMITS, TOOLS } from '@/lib/constants'

describe('APP_VERSION', () => {
  it('should be defined', () => {
    expect(APP_VERSION).toBeDefined()
    expect(typeof APP_VERSION).toBe('string')
  })
})

describe('PLAN_LIMITS', () => {
  it('should define limits for free plan', () => {
    expect(PLAN_LIMITS.free).toBeDefined()
    expect(PLAN_LIMITS.free.maxLinesMonth).toBe(1200)
  })

  it('should define limits for pro plan', () => {
    expect(PLAN_LIMITS.pro).toBeDefined()
    expect(PLAN_LIMITS.pro.maxLinesMonth).toBeNull()
  })
})

describe('TOOLS', () => {
  it('should contain all expected tools', () => {
    expect(TOOLS).toBeDefined()
    expect(TOOLS.length).toBeGreaterThan(0)
  })

  it('each tool should have required fields', () => {
    TOOLS.forEach(tool => {
      expect(tool.id).toBeDefined()
      expect(tool.name).toBeDefined()
      expect(tool.description).toBeDefined()
      expect(tool.icon).toBeDefined()
    })
  })
})
