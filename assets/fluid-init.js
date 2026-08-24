// Фоновая WebGL-жидкость в бирюзово-зелёной палитре портфолио.
// Цвет каждого «сплата» берётся из generateColor() внутри fluid.js,
// поэтому переопределяем её: оттенок 150°–172° (зелёный → бирюзовый).
window.generateColor = function () {
  const c = HSVtoRGB(0.42 + Math.random() * 0.10, 0.85, 1.0);
  c.r *= 0.22;
  c.g *= 0.22;
  c.b *= 0.22;
  return c;
};

// Оживляем фон без курсора: периодические случайные сплаты.
setInterval(function () {
  try {
    multipleSplats(2 + Math.floor(Math.random() * 3));
  } catch (e) {}
}, 2800);
