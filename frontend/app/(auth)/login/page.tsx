import { Metadata } from 'next';
import { generateMetadata as generateSEOMetadata } from '@/lib/seo';
import LoginPageClient from './LoginPageClient';

export const metadata: Metadata = generateSEOMetadata({
  title: 'Sign In',
  description: 'Sign in to your Price Watchdogs account to monitor SaaS pricing changes and manage your subscriptions.',
  path: '/login',
  keywords: ['login', 'sign in', 'account access', 'SaaS monitoring login'],
  noIndex: true,
});

export default function LoginPage() {
  return <LoginPageClient />;
}
