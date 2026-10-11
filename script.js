// Carousels: hero (autoplay) and the three gallery albums (with thumbnails)
(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  Array.prototype.forEach.call(document.querySelectorAll('.cz'), function (root) {
    var slides = root.querySelectorAll('.cz__slide');
    var thumbs = root.querySelectorAll('.cz__thumbs button');
    var count = root.querySelector('.cz__count');
    var cap = root.querySelector('.cz__cap');
    var stage = root.querySelector('.cz__stage');
    var i = 0, timer = null, x0 = null;
    if (!slides.length) return;

    function show(n) {
      slides[i].classList.remove('is-on');
      if (thumbs[i]) thumbs[i].removeAttribute('aria-current');
      i = (n + slides.length) % slides.length;
      slides[i].classList.add('is-on');
      if (thumbs[i]) {
        thumbs[i].setAttribute('aria-current', 'true');
        thumbs[i].scrollIntoView({ block: 'nearest', inline: 'nearest' });
      }
      var img = slides[i].querySelector('img');
      img.loading = 'eager';
      count.textContent = (i + 1) + ' / ' + slides.length;
      cap.textContent = img.alt;
    }
    function play() {
      if (!root.hasAttribute('data-auto') || reduce) return;
      clearInterval(timer);
      timer = setInterval(function () { show(i + 1); }, 5000);
    }
    function stop() { clearInterval(timer); }

    root.querySelector('.cz__prev').addEventListener('click', function () { show(i - 1); play(); });
    root.querySelector('.cz__next').addEventListener('click', function () { show(i + 1); play(); });
    Array.prototype.forEach.call(thumbs, function (b, n) {
      b.addEventListener('click', function () { show(n); });
    });
    stage.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var d = e.changedTouches[0].clientX - x0;
      if (Math.abs(d) > 40) { show(i + (d < 0 ? 1 : -1)); play(); }
      x0 = null;
    });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { show(i - 1); play(); }
      if (e.key === 'ArrowRight') { show(i + 1); play(); }
    });
    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', play);
    root.addEventListener('focusin', stop);

    // Mark the first slide visible without JS-dependent flash
    show(0);
    play();
  });
})();
