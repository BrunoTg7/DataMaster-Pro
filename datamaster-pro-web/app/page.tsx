import { HeroSection, BenefitsSection } from '@/components/landing/Hero'
import { ToolsSection } from '@/components/landing/ToolsGrid'
import { TestimonialsSection, CTASection } from '@/components/landing/Sections'

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <BenefitsSection />
      <ToolsSection />
      <TestimonialsSection />
      <CTASection />
    </>
  )
}