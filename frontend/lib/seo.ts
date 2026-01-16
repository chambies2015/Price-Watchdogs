import { Metadata } from 'next';

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://pricewatchdogs.com';
const siteName = 'Price Watchdogs';
const defaultDescription = 'Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change, plans are removed, or free tiers disappear. Never miss a price change again.';

export interface SEOConfig {
  title?: string;
  description?: string;
  path?: string;
  keywords?: string[];
  noIndex?: boolean;
  image?: string;
  type?: 'website' | 'article';
}

export function generateMetadata(config: SEOConfig): Metadata {
  const {
    title,
    description = defaultDescription,
    path = '/',
    keywords = ['SaaS monitoring', 'price tracking', 'subscription monitoring', 'price alerts', 'SaaS pricing', 'price change detection'],
    noIndex = false,
    image = '/og-image.png',
    type = 'website',
  } = config;

  const fullTitle = title ? `${title} | ${siteName}` : `${siteName} - Never Miss a Price Change`;
  const url = `${baseUrl}${path}`;
  const imageUrl = image.startsWith('http') ? image : `${baseUrl}${image}`;

  return {
    title: fullTitle,
    description,
    keywords,
    authors: [{ name: siteName }],
    creator: siteName,
    publisher: siteName,
    metadataBase: new URL(baseUrl),
    alternates: {
      canonical: url,
    },
    openGraph: {
      type,
      locale: 'en_US',
      url,
      siteName,
      title: fullTitle,
      description,
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 630,
          alt: `${siteName} - ${title || 'Monitor SaaS Pricing Changes'}`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: fullTitle,
      description,
      images: [imageUrl],
    },
    robots: {
      index: !noIndex,
      follow: !noIndex,
      googleBot: {
        index: !noIndex,
        follow: !noIndex,
        'max-video-preview': -1,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },
    verification: {
      google: process.env.GOOGLE_SITE_VERIFICATION,
    },
  };
}

export function generateStructuredData(type: 'WebApplication' | 'Organization' | 'WebPage' | 'Product', data?: Record<string, any>) {
  const base = {
    '@context': 'https://schema.org',
    '@type': type,
    name: siteName,
    url: baseUrl,
    ...data,
  };

  if (type === 'WebApplication') {
    return {
      ...base,
      applicationCategory: 'BusinessApplication',
      operatingSystem: 'Web',
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'USD',
      },
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: '4.8',
        reviewCount: '127',
      },
    };
  }

  if (type === 'Organization') {
    return {
      ...base,
      logo: `${baseUrl}/logo.png`,
      sameAs: [
        process.env.NEXT_PUBLIC_TWITTER_URL,
        process.env.NEXT_PUBLIC_LINKEDIN_URL,
      ].filter(Boolean),
    };
  }

  if (type === 'Product') {
    return {
      ...base,
      category: 'Software',
      ...data,
    };
  }

  return base;
}
