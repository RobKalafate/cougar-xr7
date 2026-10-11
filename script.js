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
