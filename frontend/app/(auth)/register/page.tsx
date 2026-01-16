import { Metadata } from 'next';
import { generateMetadata as generateSEOMetadata } from '@/lib/seo';
import RegisterPageClient from './RegisterPageClient';

export const metadata: Metadata = generateSEOMetadata({
  title: 'Create Account',
  description: 'Create your free Price Watchdogs account and start monitoring SaaS pricing changes. No credit card required.',
  path: '/register',
  keywords: ['sign up', 'register', 'create account', 'free trial', 'SaaS monitoring signup'],
});

export default function RegisterPage() {
  return <RegisterPageClient />;
}
