import { motion } from 'framer-motion';
import { Shield, ChevronLeft } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';

export default function PrivacyPage() {
  const { state } = useApp();
  const dispatch = useDispatch();
  const loginDate = state.loginDate || new Date().toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' });

  return (
    <motion.div className="page-wrapper legal-page"
      initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}
      transition={{ duration:0.35 }}>

      <button className="legal-back-btn" onClick={() => dispatch({ type:'SET_PAGE', payload:'settings' })}>
        <ChevronLeft size={15} /> Back to Settings
      </button>

      <div className="page-header-row">
        <div>
          <div className="page-eyebrow"><Shield size={11} /> Legal</div>
          <h1 className="page-title">Privacy Policy</h1>
          <p className="page-subtitle">Effective Date: {loginDate}</p>
        </div>
        <div className="page-title-icon"><Shield size={22} /></div>
      </div>

      <div className="glass-card legal-card">
        <p className="legal-intro">Welcome to <strong>RECO</strong> ("we," "our," or "us"). Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your information when you use our AI shopping assistant.</p>

        <LegalSection num="1" title="Information We Collect">
          <p>We may collect the following types of information:</p>
          <LegalSub title="a. Information You Provide">
            <ul>
              <li>Search queries and product preferences</li>
              <li>Account details (such as name and email, if you sign up)</li>
            </ul>
          </LegalSub>
          <LegalSub title="b. Automatically Collected Information">
            <ul>
              <li>Device information (browser type, IP address)</li>
              <li>Usage data (pages visited, interactions)</li>
              <li>Cookies and similar technologies</li>
            </ul>
          </LegalSub>
        </LegalSection>

        <LegalSection num="2" title="How We Use Your Information">
          <p>We use your data to:</p>
          <ul>
            <li>Provide and improve AI-generated recommendations</li>
            <li>Personalize your experience</li>
            <li>Analyze usage and improve performance</li>
            <li>Maintain security and prevent misuse</li>
          </ul>
        </LegalSection>

        <LegalSection num="3" title="AI & Automated Processing">
          <p>RECO uses artificial intelligence to generate product recommendations. These recommendations are automated and may not always be accurate, complete, or suitable for your needs.</p>
        </LegalSection>

        <LegalSection num="4" title="Third-Party Services">
          <p>We may use third-party services such as:</p>
          <ul>
            <li>AI providers</li>
            <li>Analytics tools (e.g., traffic analysis)</li>
            <li>Affiliate platforms</li>
          </ul>
          <p>These services may process data according to their own privacy policies.</p>
        </LegalSection>

        <LegalSection num="5" title="Data Sharing">
          <p>We do not sell your personal data. We may share data with trusted service providers only when necessary to operate our service.</p>
        </LegalSection>

        <LegalSection num="6" title="Data Retention">
          <p>We retain your information only as long as necessary to:</p>
          <ul>
            <li>Provide our services</li>
            <li>Improve user experience</li>
            <li>Comply with legal obligations</li>
          </ul>
        </LegalSection>

        <LegalSection num="7" title="Your Rights">
          <p>You may:</p>
          <ul>
            <li>Request access to your data</li>
            <li>Request deletion of your data</li>
            <li>Stop using the service at any time</li>
          </ul>
          <p>To request data removal, contact us at: <a href="mailto:asamir1000samira@gmail.com" className="legal-link">asamir1000samira@gmail.com</a></p>
        </LegalSection>

        <LegalSection num="8" title="Security">
          <p>We implement reasonable safeguards to protect your data. However, no system is completely secure.</p>
        </LegalSection>

        <LegalSection num="9" title="Changes to This Policy">
          <p>We may update this Privacy Policy from time to time. Updates will be posted with a new effective date.</p>
        </LegalSection>

        <LegalSection num="10" title="Contact Us">
          <p>If you have questions, contact us at: <a href="mailto:asamir1000samira@gmail.com" className="legal-link">asamir1000samira@gmail.com</a></p>
        </LegalSection>

        <div className="legal-agreement">By using RECO, you agree to this Privacy Policy.</div>
        <div className="legal-footer">&copy; 2026 RECO AI — All rights reserved</div>
      </div>
    </motion.div>
  );
}

function LegalSection({ num, title, children }: { num: string; title: string; children: React.ReactNode }) {
  return (
    <div className="legal-section">
      <h2 className="legal-section-title"><span className="legal-num">{num}.</span> {title}</h2>
      <div className="legal-section-body">{children}</div>
    </div>
  );
}

function LegalSub({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="legal-sub">
      <h4 className="legal-sub-title">{title}</h4>
      {children}
    </div>
  );
}
