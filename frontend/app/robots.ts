import { MetadataRoute } from 'next';

export const dynamic = 'force-static';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://pricewatchdogs.com';

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/api/',
          '/dashboard/',
          '/billing/',
          '/services/',
          '/checkout/',
          '/home/',
        ],
      },
      {
        userAgent: 'Googlebot',
        allow: '/',
        disallow: [
          '/api/',
          '/dashboard/',
          '/billing/',
          '/services/',
          '/checkout/',
          '/home/',
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
