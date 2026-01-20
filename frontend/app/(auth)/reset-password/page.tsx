import ResetPasswordPageClient from './pageClient';
import { Suspense } from 'react';

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordPageClient />
    </Suspense>
  );
}

