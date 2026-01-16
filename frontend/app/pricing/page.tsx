import { Metadata } from 'next';
import { generateMetadata as generateSEOMetadata, generateStructuredData } from '@/lib/seo';
import PricingPageClient from './PricingPageClient';

export const metadata: Metadata = generateSEOMetadata({
  title: 'Pricing',
  description: 'Simple, transparent pricing for Price Watchdogs. Start free with up to 3 services, or upgrade to Pro for unlimited monitoring. No credit card required.',
  path: '/pricing',
  keywords: ['pricing', 'subscription plans', 'SaaS pricing', 'price monitoring cost', 'free trial'],
});

export default function PricingPage() {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://pricewatchdogs.com';
  
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: 'Price Watchdogs',
    description: 'Professional SaaS price monitoring with unlimited services and advanced features',
    category: 'Software as a Service',
    url: `${baseUrl}/pricing`,
    offers: [
      {
        '@type': 'Offer',
        name: 'Free Plan',
        price: '0',
        priceCurrency: 'USD',
        availability: 'https://schema.org/InStock',
      },
      {
        '@type': 'Offer',
        name: 'Pro Monthly',
        price: '5',
        priceCurrency: 'USD',
        priceSpecification: {
          '@type': 'UnitPriceSpecification',
          price: '5',
          priceCurrency: 'USD',
          billingDuration: 'P1M',
        },
        availability: 'https://schema.org/InStock',
      },
      {
        '@type': 'Offer',
        name: 'Pro Annual',
        price: '50',
        priceCurrency: 'USD',
        priceSpecification: {
          '@type': 'UnitPriceSpecification',
          price: '50',
          priceCurrency: 'USD',
          billingDuration: 'P1Y',
        },
        availability: 'https://schema.org/InStock',
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <PricingPageClient />
    </>
  );
}
