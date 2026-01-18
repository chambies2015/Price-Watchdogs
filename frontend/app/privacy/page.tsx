export default function PrivacyPage() {
  return (
    <main className="app-content">
      <div className="privacy-page">
        <h1>Privacy Policy</h1>
        <p>
          Price Watchdogs respects your privacy. This policy explains what we
          collect, how we use it, and the choices you have.
        </p>
        <h2>Information We Collect</h2>
        <ul>
          <li>Account information such as email address and password.</li>
          <li>Service URLs and configuration you provide.</li>
          <li>Usage data such as requests, errors, and performance metrics.</li>
          <li>Payment details are processed by Stripe and not stored by us.</li>
        </ul>
        <h2>How We Use Information</h2>
        <ul>
          <li>Provide and improve the service.</li>
          <li>Authenticate users and secure accounts.</li>
          <li>Send service emails like password resets.</li>
          <li>Monitor reliability, security, and performance.</li>
        </ul>
        <h2>Data Sharing</h2>
        <ul>
          <li>We do not sell your data.</li>
          <li>We share data with providers only to operate the service.</li>
        </ul>
        <h2>Data Retention</h2>
        <p>
          We retain data while your account is active or as needed to provide
          the service. You may request deletion by contacting support.
        </p>
        <h2>Your Choices</h2>
        <ul>
          <li>You can update your account information in the app.</li>
          <li>You can request account deletion via support.</li>
        </ul>
        <h2>Contact</h2>
        <p>
          For privacy questions, email{" "}
          <a href="mailto:pricewatchdogs@gmail.com">pricewatchdogs@gmail.com</a>.
        </p>
        <p>Last updated: January 17, 2026</p>
      </div>
    </main>
  );
}
