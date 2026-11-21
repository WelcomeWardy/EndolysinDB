/**
 * main.js — EndolysinDB client-side utilities
 * Sidebar toggle, active-nav highlighting, minor UX helpers.
 */

document.addEventListener('DOMContentLoaded', function () {

  // ---------------------------------------------------------------
  // Sidebar toggle (mobile)
  // ---------------------------------------------------------------
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebar-overlay');

  function openSidebar() {
    sidebar.classList.add('show');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('show');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.contains('show') ? closeSidebar() : openSidebar();
    });
  }

  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on nav link click (mobile)
  if (sidebar) {
    sidebar.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth < 768) closeSidebar();
      });
    });
  }

  // ---------------------------------------------------------------
  // Highlight active sidebar link based on current path
  // (Jinja2 sets .active via request.endpoint, but this provides
  //  a client-side fallback for edge cases.)
  // ---------------------------------------------------------------
  const currentPath = window.location.pathname;
  if (sidebar) {
    sidebar.querySelectorAll('a').forEach(function (link) {
      const href = link.getAttribute('href');
      if (href && href !== '#' && currentPath.startsWith(href) && href !== '/') {
        link.classList.add('active');
      }
    });
  }

  // ---------------------------------------------------------------
  // Auto-dismiss flash alerts after 5 s
  // ---------------------------------------------------------------
  document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

});
