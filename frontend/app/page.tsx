import { Metadata } from 'next';
import { generateMetadata as generateSEOMetadata, generateStructuredData } from '@/lib/seo';
import HomePageClient from './HomePageClient';

export const metadata: Metadata = generateSEOMetadata({
  title: 'Never Miss a Price Change',
  path: '/',
});

export default function Home() {
  const structuredData = generateStructuredData('WebApplication', {
    description: 'Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change, plans are removed, or free tiers disappear.',
    featureList: [
      'Automated Monitoring',
      'Smart Change Detection',
      'Instant Alerts',
      'Change History',
      'Multiple Services',
      'Privacy First'
    ],
  });

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <HomePageClient />
    </>
  );
}
