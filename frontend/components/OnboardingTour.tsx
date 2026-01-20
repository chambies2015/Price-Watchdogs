'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

const STORAGE_KEY = 'pw_onboarding_v1';

interface Step {
  title: string;
  body: string;
}

const steps: Step[] = [
  {
    title: 'Add your first service',
    body: 'Start by adding a pricing page you want to monitor. We will check it on a schedule and alert you on changes.',
  },
  {
    title: 'Track health at a glance',
    body: 'Each service shows its status, last check, and next check so you know it is running.',
  },
  {
    title: 'Review changes quickly',
    body: 'Open a service to see the latest change summary and snapshots.',
  },
];

export default function OnboardingTour() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const seen = window.localStorage.getItem(STORAGE_KEY);
    if (!seen) {
      setOpen(true);
    }
  }, []);

  const handleClose = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, 'seen');
    }
    setOpen(false);
  };

  if (!open) return null;

  const current = steps[step];
  const isLast = step === steps.length - 1;

  return (
    <div className="tour-overlay" role="dialog" aria-modal="true" onClick={handleClose}>
      <div className="tour-card" onClick={(e) => e.stopPropagation()}>
        <button className="tour-close" onClick={handleClose} aria-label="Close tour">
          ×
        </button>
        <div className="tour-step">Step {step + 1} of {steps.length}</div>
        <h2 className="tour-title">{current.title}</h2>
        <p className="tour-body">{current.body}</p>
        <div className="tour-actions">
          <button className="tour-skip" onClick={handleClose}>
            Skip tour
          </button>
          <div className="tour-cta">
            {step === 0 && (
              <Link href="/services/new" className="tour-link">
                Add Service
              </Link>
            )}
            {!isLast ? (
              <button className="tour-next" onClick={() => setStep(step + 1)}>
                Next
              </button>
            ) : (
              <button className="tour-next" onClick={handleClose}>
                Finish
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
