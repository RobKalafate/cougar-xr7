// Lightbox for the gallery
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('.grid .g'));
  var lb = document.getElementById('lb');
  if (!lb || !links.length) return;
  var img = lb.querySelector('img'), cap = lb.querySelector('.lb__c'), i = 0;

  function show(n) {
    i = (n + links.length) % links.length;
    img.src = links[i].getAttribute('href');
    img.alt = links[i].querySelector('img').alt;
    cap.textContent = links[i].querySelector('span').textContent + '  ·  ' + (i + 1) + ' / ' + links.length;
  }
  links.forEach(function (a, n) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      show(n);
      lb.showModal();
    });
  });
  lb.querySelector('.lb__x').onclick = function () { lb.close(); };
  lb.querySelector('.lb__p').onclick = function () { show(i - 1); };
  lb.querySelector('.lb__n').onclick = function () { show(i + 1); };
  lb.addEventListener('click', function (e) { if (e.target === lb) lb.close(); });
  document.addEventListener('keydown', function (e) {
    if (!lb.open) return;
    if (e.key === 'ArrowLeft') show(i - 1);
    if (e.key === 'ArrowRight') show(i + 1);
  });
})();

// Hero carousel
(function () {
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  if (!slides.length) return;
  var count = document.querySelector('.car__count'), cap = document.querySelector('.car__cap'), i = 0, t;
  function show(n) {
    slides[i].classList.remove('is-on');
    i = (n + slides.length) % slides.length;
    slides[i].classList.add('is-on');
    count.textContent = (i + 1) + ' / ' + slides.length;
    cap.textContent = slides[i].querySelector('img').alt.replace(/^[^:]*: /, '');
  }
  function auto() { clearInterval(t); if (!matchMedia('(prefers-reduced-motion: reduce)').matches) t = setInterval(function () { show(i + 1); }, 5000); }
  document.querySelector('.car__prev').onclick = function () { show(i - 1); auto(); };
  document.querySelector('.car__next').onclick = function () { show(i + 1); auto(); };
  var st = document.querySelector('.carousel__stage'), x0 = null;
  st.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  st.addEventListener('touchend', function (e) { if (x0 === null) return; var d = e.changedTouches[0].clientX - x0; if (Math.abs(d) > 40) { show(i + (d < 0 ? 1 : -1)); auto(); } x0 = null; });
  st.addEventListener('mouseenter', function () { clearInterval(t); });
  st.addEventListener('mouseleave', auto);
  show(0); auto();
})();
