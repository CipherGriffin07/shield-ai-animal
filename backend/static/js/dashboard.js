/**
 * SHIELD AI — Dashboard shell
 * Renders the sidebar for the current role and guards the page behind auth.
 * Call renderDashboardShell({ active: 'overview' }) at the top of each
 * dashboard page's script, after api.js is loaded.
 */
const ICONS = {
  overview: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>',
  report: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2 4 5.5V11c0 5.5 3.4 9.9 8 11 4.6-1.1 8-5.5 8-11V5.5L12 2z"/></svg>',
  track: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></svg>',
  cases: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
  lostfound: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/></svg>',
  adopt: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 12l2 2 4-4"/><rect x="3" y="4" width="18" height="16" rx="2"/></svg>',
  chat: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4h16v12H7l-3 3V4z"/></svg>',
  settings: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.6 1H21a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1z"/></svg>',
  users: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  analytics: '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/></svg>',
};

const NAV_BY_ROLE = {
  citizen: [
    { href: '/dashboard', key: 'overview', label: 'Overview', icon: 'overview' },
    { href: '/report', key: 'report', label: 'Report an animal', icon: 'report' },
    { href: '/tracking', key: 'track', label: 'Track a rescue', icon: 'track' },
    { href: '/lost-found', key: 'lostfound', label: 'Lost & found', icon: 'lostfound' },
    { href: '/adoption', key: 'adopt', label: 'Adoption', icon: 'adopt' },
    { href: '/chatbot', key: 'chat', label: 'Ask SHIELD', icon: 'chat' },
    { href: '/settings', key: 'settings', label: 'Settings', icon: 'settings' },
  ],
  volunteer: [
    { href: '/volunteer', key: 'overview', label: 'Nearby cases', icon: 'overview' },
    { href: '/tracking', key: 'track', label: 'Track a rescue', icon: 'track' },
    { href: '/chatbot', key: 'chat', label: 'Ask SHIELD', icon: 'chat' },
    { href: '/settings', key: 'settings', label: 'Settings', icon: 'settings' },
  ],
  ngo: [
    { href: '/ngo', key: 'overview', label: 'Incoming cases', icon: 'overview' },
    { href: '/adoption', key: 'adopt', label: 'Adoption listings', icon: 'adopt' },
    { href: '/settings', key: 'settings', label: 'Settings', icon: 'settings' },
  ],
  veterinarian: [
    { href: '/ngo', key: 'overview', label: 'Incoming cases', icon: 'overview' },
    { href: '/settings', key: 'settings', label: 'Settings', icon: 'settings' },
  ],
  admin: [
    { href: '/admin', key: 'overview', label: 'Analytics', icon: 'analytics' },
    { href: '/admin#users', key: 'users', label: 'Users & NGOs', icon: 'users' },
    { href: '/settings', key: 'settings', label: 'Settings', icon: 'settings' },
  ],
};

async function renderDashboardShell({ active, title } = {}) {
  requireAuth();
  const shell = document.getElementById('dash-shell');
  if (!shell) return null;

  let user;
  try { user = await SHIELD_API.me(); }
  catch { logout(); return null; }

  const nav = NAV_BY_ROLE[user.role] || NAV_BY_ROLE.citizen;
  const initials = user.full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();

  shell.innerHTML = `
    <aside class="dash-sidebar">
      <a class="brand" href="/">
        <span class="brand-mark"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 2L4 5.5V11C4 16.5 7.4 20.9 12 22C16.6 20.9 20 16.5 20 11V5.5L12 2Z" fill="white" fill-opacity="0.95"/><path d="M9 12L11 14L15.5 9.5" stroke="#0E3320" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
        SHIELD AI
      </a>
      <nav class="dash-nav">
        ${nav.map(item => `<a href="${item.href}" class="${item.key === active ? 'active' : ''}">${ICONS[item.icon]}${item.label}</a>`).join('')}
      </nav>
      <div class="dash-user">
        <div class="avatar">${initials}</div>
        <div>
          <div class="name">${user.full_name}</div>
          <div class="role">${user.role}</div>
        </div>
        <button onclick="logout()" title="Log out">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
        </button>
      </div>
    </aside>
    <main class="dash-main">
      <div class="dash-topbar">
        <h1>${title || ''}</h1>
        <a class="btn btn-secondary" href="/">Visit site →</a>
      </div>
      <div class="dash-content" id="dash-content"></div>
    </main>
  `;
  return user;
}

function showToast(message) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), 3000);
}

function severityBadgeClass(severity) {
  return { Low: 'badge-low', Moderate: 'badge-moderate', High: 'badge-high', Critical: 'badge-critical' }[severity] || 'badge-low';
}

function timeAgo(dateStr) {
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
