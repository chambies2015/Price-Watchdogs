import ServiceDetailClient from '@/components/ServiceDetailClient';

export async function generateStaticParams() {
  return [];
}

export const dynamicParams = true;

export default function ServiceDetailPage({ params }: { params: { id: string } }) {
  return <ServiceDetailClient serviceId={params.id} />;
}
