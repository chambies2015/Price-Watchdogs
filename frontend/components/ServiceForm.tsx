'use client';

import { useState, useEffect } from 'react';
import { Service, ServiceCreate, ServiceUpdate, CheckFrequency, subscriptionsApi, Subscription } from '@/lib/api';
import Link from 'next/link';
import TagManager from './TagManager';

interface ServiceFormProps {
  initialData?: Service;
  onSubmit: (data: ServiceCreate | ServiceUpdate) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
}

export default function ServiceForm({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: ServiceFormProps) {
  const presets = [
    { id: 'custom', label: 'Custom', name: '', url: '' },
    { id: 'netflix', label: 'Netflix', name: 'Netflix', url: 'https://www.netflix.com/signup?serverState=%7B%22realm%22%3A%22growth%22%2C%22name%22%3A%22PLAN_SELECTION%22%2C%22clcsSessionId%22%3A%223c446b7f-661e-4ea2-9320-ae6900ce3e5d%22%2C%22sessionContext%22%3A%7B%22session-breadcrumbs%22%3A%7B%22funnel_name%22%3A%22signupSimplicity%22%7D%7D%7D' },
    { id: 'disney_plus', label: 'Disney+', name: 'Disney+', url: 'https://www.disneyplus.com/commerce/plans' },
    { id: 'hulu', label: 'Hulu', name: 'Hulu', url: 'https://help.hulu.com/article/hulu-how-much-does-hulu-cost' },
    { id: 'youtube_tv', label: 'YouTube TV', name: 'YouTube TV', url: 'https://tv.youtube.com/welcome/#plans' },
    { id: 'max', label: 'Max (HBO Max)', name: 'Max', url: 'https://help.hbomax.com/us/Answer/Detail/000002547' },
    { id: 'prime_video', label: 'Amazon Prime', name: 'Amazon Prime', url: 'https://www.amazon.com/amazonprime' },
    { id: 'apple_tv_plus', label: 'Apple TV+', name: 'Apple TV+', url: 'https://www.apple.com/apple-tv/' },
    { id: 'paramount_plus', label: 'Paramount+', name: 'Paramount+', url: 'https://www.paramountplus.com/account/signup/pickplan/' },
    { id: 'peacock', label: 'Peacock', name: 'Peacock', url: 'https://www.peacocktv.com/plans/all-monthly' },
    { id: 'spotify', label: 'Spotify Premium', name: 'Spotify Premium', url: 'https://www.spotify.com/us/premium/' },
  ] as const;

  const [presetId, setPresetId] = useState<string>('custom');
  const [name, setName] = useState(initialData?.name || '');
  const [url, setUrl] = useState(initialData?.url || '');
  const [checkFrequency, setCheckFrequency] = useState<CheckFrequency>(
    initialData?.check_frequency || 'daily'
  );
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);
  const [alertsEnabled, setAlertsEnabled] = useState(initialData?.alerts_enabled ?? true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(
    initialData?.alert_confidence_threshold ?? 0.6
  );
  const [slackWebhookUrl, setSlackWebhookUrl] = useState(initialData?.slack_webhook_url || '');
  const [discordWebhookUrl, setDiscordWebhookUrl] = useState(initialData?.discord_webhook_url || '');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(initialData?.tags?.map(t => t.id) || []);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loadingSubscription, setLoadingSubscription] = useState(false);

  useEffect(() => {
    if (!initialData) {
      loadSubscription();
    }
  }, [initialData]);

  const loadSubscription = async () => {
    try {
      setLoadingSubscription(true);
      const sub = await subscriptionsApi.getCurrent();
      setSubscription(sub);
    } catch (err) {
      console.error('Error loading subscription:', err);
    } finally {
      setLoadingSubscription(false);
    }
  };

  const getAllowedFrequencies = (): CheckFrequency[] => {
    if (!subscription) return ['daily', 'weekly'];
    if (subscription.plan_type === 'free') {
      return ['daily', 'weekly'];
    }
    return ['daily', 'weekly', 'twice_daily'];
  };

  const isAtLimit = (): boolean => {
    if (!subscription) return false;
    if (subscription.service_limit === null) return false;
    return subscription.current_service_count >= subscription.service_limit;
  };

  const canUseFrequency = (freq: CheckFrequency): boolean => {
    return getAllowedFrequencies().includes(freq);
  };

  const validateUrl = (urlValue: string): boolean => {
    try {
      new URL(urlValue);
      return urlValue.startsWith('http://') || urlValue.startsWith('https://');
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!name.trim()) {
      setError('Service name is required');
      return;
    }
    
    if (!url.trim()) {
      setError('URL is required');
      return;
    }
    
    if (!validateUrl(url)) {
      setError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    
    setLoading(true);
    
    try {
      if (initialData) {
        await onSubmit({
          name,
          url,
          check_frequency: checkFrequency,
          is_active: isActive,
          alerts_enabled: alertsEnabled,
          alert_confidence_threshold: confidenceThreshold,
          slack_webhook_url: slackWebhookUrl || null,
          discord_webhook_url: discordWebhookUrl || null,
          tag_ids: selectedTagIds.length > 0 ? selectedTagIds : undefined,
        });
      } else {
        await onSubmit({ 
          name, 
          url, 
          check_frequency: checkFrequency,
          tag_ids: selectedTagIds.length > 0 ? selectedTagIds : undefined,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save service');
    } finally {
      setLoading(false);
    }
  };

  const allowedFrequencies = getAllowedFrequencies();
  const atLimit = isAtLimit();

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {!initialData && subscription && atLimit && (
        <div className="rounded-md bg-yellow-50 p-4 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
          <p className="font-semibold mb-2">Service Limit Reached</p>
          <p className="mb-3">
            You have reached your service limit ({subscription.current_service_count}/{subscription.service_limit}). 
            Upgrade to Pro for unlimited services.
          </p>
          <Link
            href="/pricing"
            className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            Upgrade to Pro
          </Link>
        </div>
      )}

      {!initialData && subscription && !atLimit && subscription.service_limit !== null && (
        <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
          <p>
            You have {subscription.service_limit - subscription.current_service_count} service{subscription.service_limit - subscription.current_service_count !== 1 ? 's' : ''} remaining.
            {subscription.plan_type === 'free' && ' Upgrade to Pro for unlimited services.'}
          </p>
        </div>
      )}

      {!initialData && (
        <div>
          <label htmlFor="preset" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Preset Service
          </label>
          <select
            id="preset"
            value={presetId}
            onChange={(e) => {
              const id = e.target.value;
              setPresetId(id);
              const preset = presets.find((p) => p.id === id);
              if (!preset || preset.id === 'custom') return;
              setName(preset.name);
              setUrl(preset.url);
            }}
            className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
          >
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Selecting a preset auto-fills the name and URL. You can still edit both fields.
          </p>
        </div>
      )}
      
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Service Name
        </label>
        <input
          id="name"
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
          placeholder="e.g., Stripe Pricing"
        />
      </div>
      
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Pricing Page URL
        </label>
        <input
          id="url"
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
          placeholder="https://example.com/pricing"
        />
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
          The URL of the pricing or plans page to monitor
        </p>
      </div>
      
      <div>
        <label htmlFor="frequency" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Check Frequency
        </label>
        <select
          id="frequency"
          value={checkFrequency}
          onChange={(e) => {
            const newFreq = e.target.value as CheckFrequency;
            if (canUseFrequency(newFreq)) {
              setCheckFrequency(newFreq);
            }
          }}
          disabled={atLimit && !initialData}
          className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          {allowedFrequencies.includes('twice_daily') && (
            <option value="twice_daily">Twice Daily (Every 12 hours)</option>
          )}
        </select>
        {subscription && subscription.plan_type === 'free' && checkFrequency === 'twice_daily' && (
          <p className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
            Twice-daily checks are only available for Pro plans.{' '}
            <Link href="/pricing" className="underline hover:no-underline">
              Upgrade to Pro
            </Link>
          </p>
        )}
        {!allowedFrequencies.includes(checkFrequency) && (
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">
            This frequency is not available for your current plan.
          </p>
        )}
      </div>
      
      {initialData && (
        <>
          <div className="flex items-center">
            <input
              id="is_active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300 text-zinc-600 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800"
            />
            <label htmlFor="is_active" className="ml-2 block text-sm text-zinc-700 dark:text-zinc-300">
              Active (monitoring enabled)
            </label>
          </div>
          
          <div className="space-y-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800/50">
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Alert Settings</h3>
            
            <div className="flex items-center">
              <input
                id="alerts_enabled"
                type="checkbox"
                checked={alertsEnabled}
                onChange={(e) => setAlertsEnabled(e.target.checked)}
                className="h-4 w-4 rounded border-zinc-300 text-zinc-600 focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800"
              />
              <label htmlFor="alerts_enabled" className="ml-2 block text-sm text-zinc-700 dark:text-zinc-300">
                Enable email alerts
              </label>
            </div>
            
            {alertsEnabled && (
              <>
                <div>
                  <label htmlFor="confidence_threshold" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Confidence Threshold
                  </label>
                  <input
                    id="confidence_threshold"
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={confidenceThreshold}
                    onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value) || 0.6)}
                    className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    Only send alerts for changes with confidence above this threshold (0.0 - 1.0)
                  </p>
                </div>
                {initialData && (
                  <>
                    <div>
                      <label htmlFor="slack_webhook" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Slack Webhook URL (optional)
                      </label>
                      <input
                        id="slack_webhook"
                        type="url"
                        value={slackWebhookUrl}
                        onChange={(e) => setSlackWebhookUrl(e.target.value)}
                        placeholder="https://hooks.slack.com/services/..."
                        className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
                      />
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                        Receive alerts in Slack. Leave empty to disable.
                      </p>
                    </div>
                    <div>
                      <label htmlFor="discord_webhook" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Discord Webhook URL (optional)
                      </label>
                      <input
                        id="discord_webhook"
                        type="url"
                        value={discordWebhookUrl}
                        onChange={(e) => setDiscordWebhookUrl(e.target.value)}
                        placeholder="https://discord.com/api/webhooks/..."
                        className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-zinc-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-50 sm:text-sm"
                      />
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                        Receive alerts in Discord. Leave empty to disable.
                      </p>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </>
      )}

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Tags (optional)
        </label>
        <TagManager
          onTagSelect={setSelectedTagIds}
          selectedTagIds={selectedTagIds}
          showCreate={true}
        />
      </div>
      
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading || (atLimit && !initialData) || !canUseFrequency(checkFrequency)}
          className="flex-1 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {loading ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

