import { motion } from 'framer-motion';
import { useApp, useDispatch } from '../store/AppContext';

const FULL_W = 256;
const RAIL_W = 52;

export default function SidebarToggle() {
  const { state } = useApp();
  const dispatch = useDispatch();
  const open = state.sidebarOpen;
  const isRTL = state.lang === 'ar';

  const pos = open ? FULL_W : RAIL_W;

  return (
    <motion.button
      className="claude-sidebar-toggle"
      onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
      title={open ? (isRTL ? 'طي الشريط الجانبي' : 'Collapse sidebar') : (isRTL ? 'توسيع الشريط الجانبي' : 'Expand sidebar')}
      animate={isRTL
        ? { right: pos, left: 'auto' }
        : { left: pos, right: 'auto' }
      }
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      whileHover="hovered"
    >
      <span className="cst-track">
        <motion.svg
          width="11" height="11"
          viewBox="0 0 11 11"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          animate={{
            rotate: isRTL
              ? (open ? 0 : 180)
              : (open ? 180 : 0)
          }}
          transition={{ duration: 0.25 }}
        >
          <path
            d="M4 2 L7 5.5 L4 9"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </motion.svg>
      </span>
    </motion.button>
  );
}
