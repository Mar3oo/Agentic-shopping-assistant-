import { motion } from 'framer-motion';
import { ExternalLink, Check, ShoppingBag } from 'lucide-react';
import type { Product } from '../store/AppContext';

// Curated Unsplash product images per category
const PRODUCT_IMAGES = [
  'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80',
  'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80',
  'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400&q=80',
  'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80',
  'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&q=80',
  'https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=400&q=80',
  'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&q=80',
  'https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&q=80',
];

function getImg(title = '', idx = 0) {
  const lower = title.toLowerCase();
  if (lower.includes('watch') || lower.includes('rolex')) return PRODUCT_IMAGES[0];
  if (lower.includes('headphone') || lower.includes('audio') || lower.includes('earphone')) return PRODUCT_IMAGES[1];
  if (lower.includes('camera') || lower.includes('photo')) return PRODUCT_IMAGES[2];
  if (lower.includes('shoe') || lower.includes('sneaker') || lower.includes('nike') || lower.includes('adidas')) return PRODUCT_IMAGES[3];
  if (lower.includes('perfume') || lower.includes('fragrance') || lower.includes('cologne')) return PRODUCT_IMAGES[4];
  if (lower.includes('laptop') || lower.includes('computer') || lower.includes('mac')) return 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&q=80';
  if (lower.includes('phone') || lower.includes('iphone') || lower.includes('samsung')) return 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&q=80';
  if (lower.includes('bag') || lower.includes('backpack')) return 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&q=80';
  return PRODUCT_IMAGES[idx % PRODUCT_IMAGES.length];
}

function fmtPrice(p: Product): string {
  if (p.price_text) return String(p.price_text);
  if (p.price == null || p.price === '') return '';
  return p.currency ? `${p.currency} ${p.price}` : String(p.price);
}

interface Props {
  products: Product[];
  title?: string;
  onSelect?: (p: Product) => void;
  selectedTitles?: string[];
  emptyText?: string;
}

const container = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };

export default function ProductCards({ products, title, onSelect, selectedTitles = [], emptyText = 'No products available.' }: Props) {
  if (!products.length) return title ? <div className="no-data">{emptyText}</div> : null;

  return (
    <div className="products-section">
      {title && (
        <div className="section-header">
          <h3 className="section-title">{title}</h3>
          <span className="badge badge-neutral">{products.length} items</span>
        </div>
      )}
      <motion.div className="product-grid" variants={container} initial="hidden" animate="show">
        {products.map((p, i) => {
          const sel = selectedTitles.includes(p.title || '');
          const price = fmtPrice(p);
          const imgSrc = getImg(p.title, i);
          return (
            <motion.div
              key={i}
              className={`product-card glass-card ${sel ? 'selected' : ''}`}
              variants={item}
              onClick={() => onSelect?.(p)}
              whileHover={{ y: -4 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {onSelect && (
                <div className="product-sel-badge">
                  {sel && <Check size={12} color="#fff" strokeWidth={3} />}
                </div>
              )}
              <div className="product-img-wrap">
                <img src={imgSrc} alt={p.title || 'Product'} loading="lazy" />
              </div>
              <div className="product-card-body">
                {p.source && <div className="product-source">{p.source}</div>}
                <div className="product-name">{p.title || 'Unnamed Product'}</div>
                {p.details_text && (
                  <div className="product-desc">{String(p.details_text).replace(/<[^>]+>/g, '')}</div>
                )}
                <div className="product-footer-row">
                  {price ? (
                    <span className="product-price">{price}</span>
                  ) : (
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--c-text-4)' }}>—</span>
                  )}
                  {p.link ? (
                    <a href={p.link} target="_blank" rel="noopener noreferrer" className="product-view-btn" onClick={e => e.stopPropagation()}>
                      View <ExternalLink size={11} />
                    </a>
                  ) : (
                    <button className="product-view-btn"><ShoppingBag size={11} /> Shop</button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
