// always show login on mobile
if ($(window).width() < 767) {
  $('.login-container').show();
}

// close login
function closeLogin() {
  $('.login-container').toggle();
  return;
}
