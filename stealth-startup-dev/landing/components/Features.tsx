import Feature from './Feature';

export default function Features() {
  return (
    <section className="bg-white">
      <div className="container mx-auto p-4 pt-6 md:p-6 lg:p-12">
        <h2 className="text-3xl md:text-4xl font-bold">Features</h2>
        <ul className="flex flex-wrap justify-center">
          <Feature title="Accurate Response" description="Our AI-powered system ensures accurate responses to 911 calls." />
          <Feature title="Fast Response Time" description="Our automated system reduces response time, saving precious minutes." />
          <Feature title="Scalability" description="Our solution is designed to handle high volumes of calls, ensuring reliability during emergencies." />
        </ul>
      </div>
    </section>
  );
}
