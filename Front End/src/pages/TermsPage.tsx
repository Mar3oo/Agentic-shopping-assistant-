import { motion } from 'framer-motion';
import { FileText, ChevronLeft } from 'lucide-react';
import { useApp, useDispatch } from '../store/AppContext';

export default function TermsPage() {
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
          <div className="page-eyebrow"><FileText size={11} /> Legal</div>
          <h1 className="page-title">Terms of Service</h1>
          <p className="page-subtitle">Effective Date: {loginDate}</p>
        </div>
        <div className="page-title-icon"><FileText size={22} /></div>
      </div>

      <div className="glass-card legal-card">
        <p className="legal-intro">Welcome to <strong>RECO</strong>. By accessing or using our service, you agree to the following Terms of Service.</p>

        <LegalSection num="1" title="Use of Service">
          <p>You agree to use RECO only for lawful purposes. You must not:</p>
          <ul>
            <li>Abuse, hack, or disrupt the system</li>
            <li>Use automated scraping or bots</li>
            <li>Misuse AI outputs</li>
          </ul>
        </LegalSection>

        <LegalSection num="2" title="AI Disclaimer">
          <p>RECO provides AI-generated recommendations for informational purposes only. We do not guarantee accuracy, completeness, or suitability of any recommendation.</p>
        </LegalSection>

        <LegalSection num="3" title="No Liability">
          <p>We are not responsible for:</p>
          <ul>
            <li>Purchase decisions made based on recommendations</li>
            <li>Product quality, pricing, or availability</li>
            <li>Any losses or damages resulting from use of our service</li>
          </ul>
        </LegalSection>

        <LegalSection num="4" title="Affiliate Disclosure">
          <p>RECO may include affiliate links. We may earn a commission when you purchase products through these links.</p>
        </LegalSection>

        <LegalSection num="5" title="Accounts">
          <p>If you create an account:</p>
          <ul>
            <li>You are responsible for your account security</li>
            <li>You must provide accurate information</li>
            <li>We may suspend accounts that violate these terms</li>
          </ul>
        </LegalSection>

        <LegalSection num="6" title="Intellectual Property">
          <p>All content, branding, and technology used in RECO are owned by us. You may not copy, modify, or distribute our content without permission.</p>
        </LegalSection>

        <LegalSection num="7" title="Termination">
          <p>We may suspend or terminate access to RECO at any time if users violate these terms.</p>
        </LegalSection>

        <LegalSection num="8" title="Changes to Terms">
          <p>We may update these Terms at any time. Continued use means you accept the updated terms.</p>
        </LegalSection>

        <LegalSection num="9" title="Governing Law">
          <p>These Terms are governed by the laws of Egypt.</p>
        </LegalSection>

        <LegalSection num="10" title="Contact">
          <p>For any questions: <a href="mailto:asamir1000samira@gmail.com" className="legal-link">asamir1000samira@gmail.com</a></p>
        </LegalSection>

        <div className="legal-agreement">By using RECO, you agree to these Terms of Service.</div>
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
