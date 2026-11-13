% m07 lab (GNU Octave / MATLAB) · Inverse problems and regularization (Tikhonov, L-curve)
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave with core functions only (fft, svd). It uses Octave's chained indexing f(x)(i);
% in MATLAB, replace it with temporary variables.
%
% This is the Octave copy of parts A-E of labs/python/m07_lab.ipynb. Run with:  octave-cli m07_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
% The "check" lines pass with the code as given; if one fails after a change, that is information.

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);
randn('seed', 7);

n = 256; L = 32; w = 0.3; dx = L / n;               % grid points, period (mm), front width (mm)
s = (0:n-1)' * dx;
m = [0:n/2-1, -n/2:-1]'; k = 2 * pi * m / L;        % wavenumbers (rad/mm), FFT order
gainf = @(h) exp(-abs(k) * h);                      % eq-m07-continuation
contf = @(x, h) real(ifft(fft(x) .* gainf(h)));
% band-limited periodic m03 front shape (2 pi / L) sum exp(-k_m a) sin(k_m s), m < n/2
km = 2 * pi * (1:n/2-1) / L;
front = @(s0, a) (2 * pi / L) * sin((s - s0) * km) * exp(-km' * a);
tissue = @(a) front(8, a) + front(18, a) - front(21, a);
x = tissue(w);
xn = norm(x);
circ = @(h) real(ifft(gainf(h)))(mod((0:n-1)' - (0:n-1), n) + 1);     % dense circulant matrix
tikf = @(b, h, lam) real(ifft(fft(b) .* gainf(h) ./ (gainf(h).^2 + lam^2)));
experr = @(h, sigma, f) [sum((1 - f).^2 .* abs(fft(x)).^2) / n, sigma^2 * sum(f.^2 ./ gainf(h).^2)];

% ------------------------------------------------------------------ Part A
disp('Part A: the forward map');
cont_err = max([max(abs(contf(x, 0.5) - tissue(w + 0.5))), max(abs(contf(x, 1) - tissue(w + 1))), max(abs(contf(x, 3) - tissue(w + 3)))]);
fprintf('  continuing width %.1f mm by h equals width %.1f + h: largest difference %.1e\n', w, w, cont_err);
check(cont_err < 1e-12, 'continuation of the m03 shape'); disp('  check passed: front of width w + h');
for h = [0.25 0.5 1]
  sv = svd(circ(h));
  fprintf('  h = %.2f mm: condition number from the SVD %.2e, formula exp(pi h / dx) = %.2e\n', h, sv(1) / sv(end), exp(pi * h / dx));
  if h <= 0.5, check(abs(sv(1) / sv(end) / exp(pi * h / dx) - 1) < 1e-5, 'condition number'); end
end
disp('  check passed: kappa = exp(pi h / dx)');

% ------------------------------------------------------------------ Part B
disp('Part B: the naive inverse and the Picard plot');
h = 1; A = circ(h); b0 = A * x; sigma = 1e-3 * max(abs(b0));
b = b0 + sigma * randn(n, 1);
naive_err = norm(A \ b - x) / xn;
fprintf('  naive inverse with 0.1%% noise: relative error %.1e\n', naive_err);
g = gainf(h); B = abs(fft(b)); B0 = abs(fft(b0)); ok = g > 1e-6 & abs(fft(x)) > 1e-8;
floor_ = median(B(g < 1e-6)) / (sigma * sqrt(n));
fprintf('  median noisy coefficient where the gain is below 1e-6: %.2f sigma sqrt(n)\n', floor_);
check(naive_err > 1e4 && max(abs(B0(ok) ./ g(ok) - abs(fft(x))(ok)) ./ abs(fft(x))(ok)) < 1e-6 && floor_ > 0.7 && floor_ < 1.0, 'Picard');
disp('  check passed: clean data meet the Picard condition; noise sets a floor');
if make_plots
  [~, o] = sort(-g); figure; semilogy(g(o), 'k', B0(o) / max(B0), '.', B(o) / max(B0), '.');
  xlabel('index'); legend('singular values', 'clean data', 'noisy data'); ylim([1e-18 10]);
end

% ------------------------------------------------------------------ Part C
disp('Part C: filters, the error budget and resolution');
lams = logspace(-6, 0, 121); h = 1; g = gainf(h); b0 = contf(x, h); sigma = 1e-2 * max(abs(b0));
E = zeros(numel(lams), 2);
for i = 1:numel(lams), E(i, :) = experr(h, sigma, g.^2 ./ (g.^2 + lams(i)^2)); end
[tot, ib] = min(sum(E, 2)); lam_best = lams(ib);
mc = 0; for r = 1:300, mc = mc + sum((tikf(b0 + sigma * randn(n, 1), h, lam_best) - x).^2) / 300; end
[~, o] = sort(abs(k)); tsvd = inf;
for c = 1:n, f = zeros(n, 1); f(o(1:c)) = 1; tsvd = min(tsvd, sum(experr(h, sigma, f))); end
fprintf('  best lambda %.1e: expected relative error %.3f, simulated %.3f; best truncated SVD %.3f\n', lam_best, sqrt(tot) / xn, sqrt(mc) / xn, sqrt(tsvd) / xn);
check(abs(mc / tot - 1) < 0.1 && abs(sqrt(tsvd / tot) - 1) < 0.15, 'error budget'); disp('  check passed: formula matches simulation');
win = s > 16.5 & s < 22.5;
npk = @(y) sum((y(win)(2:end-1) > y(win)(1:end-2)) & (y(win)(2:end-1) > y(win)(3:end)) & (y(win)(2:end-1) > 0.2 * max(y(win))));
pk = zeros(3, 2); hs = [1 2 3];
for j = 1:3
  h = hs(j); g = gainf(h); b0 = contf(x, h); sg = 1e-2 * max(abs(b0)); T = zeros(numel(lams), 1);
  for i = 1:numel(lams), T(i) = sum(experr(h, sg, g.^2 ./ (g.^2 + lams(i)^2))); end
  [~, ib] = min(T); xr = tikf(b0 + sg * randn(n, 1), h, lams(ib));
  pk(j, :) = [npk(b0), npk(xr)];
  fprintf('  h = %d mm: peaks between the close fronts recorded %d, reconstructed %d; shortest wavelength 2 pi h / ln(100) = %.1f mm\n', h, pk(j, 1), pk(j, 2), 2 * pi * h / log(100));
end
check(pk(1, 1) == 1 && pk(1, 2) == 2 && pk(3, 2) == 1, 'resolution'); disp('  check passed: 3-mm pair resolved at 1 mm, lost at 3 mm');

% ------------------------------------------------------------------ Part D
disp('Part D: choosing lambda');
lams = logspace(-7, 0, 141); A = circ(1); [U, S, V] = svd(A); sv = diag(S);
b0 = A * x; sg = 1e-2 * max(abs(b0)); b = b0 + sg * randn(n, 1); beta = U' * b;
res = zeros(size(lams)); sol = res; err = res; gv = res;
for i = 1:numel(lams)
  f = sv.^2 ./ (sv.^2 + lams(i)^2); xl = V * (f .* beta ./ sv);
  res(i) = norm((1 - f) .* beta); sol(i) = norm(xl); err(i) = norm(xl - x); gv(i) = res(i)^2 / (n - sum(f))^2;
end
[~, id] = min(abs(log(res / (sg * sqrt(n)))));                   % discrepancy on the grid
t = log(lams); X1 = log(res); Y1 = log(sol);
dX = gradient(X1, t); dY = gradient(Y1, t); ddX = gradient(dX, t); ddY = gradient(dY, t);
kap = (dX .* ddY - dY .* ddX) ./ (dX.^2 + dY.^2).^1.5; kap([1 2 end-1 end]) = -inf; [~, il] = max(kap);
[~, ig] = min(gv);
ratios = err([id il ig]) / min(err);
fprintf('  h = 1 mm, noise 1%%: error / best error: discrepancy %.2f, L-curve %.2f, GCV %.2f\n', ratios);
check(max(ratios) < 1.5, 'parameter choice'); disp('  check passed: all three rules near the best');
if make_plots
  figure; loglog(res, sol, 'k', res([id il ig]), sol([id il ig]), 'o'); xlabel('residual norm'); ylabel('solution norm');
end

% ------------------------------------------------------------------ Part E
disp('Part E: the Bayesian reading');
n2 = 20; L2 = 10; m2 = [0:n2/2-1, -n2/2:-1]'; k2 = 2 * pi * m2 / L2;
col = real(ifft(exp(-abs(k2) * 0.5))); A2 = col(mod((0:n2-1)' - (0:n2-1), n2) + 1);
se = 0.01; sx = 1; lam = se / sx;
M = A2' * A2 + lam^2 * eye(n2); Cpost = se^2 * inv(M);
K = sx^2 * A2' / (sx^2 * (A2 * A2') + se^2 * eye(n2)); Ccond = sx^2 * eye(n2) - K * A2 * sx^2;
y = A2 * randn(n2, 1) + se * randn(n2, 1);
same = norm(M \ (A2' * y) - K * y) < 1e-8 * norm(K * y) && norm(Cpost - Ccond) < 1e-8 * norm(Cpost);
hits = 0;
for r = 1:600
  xx = sx * randn(n2, 1); y = A2 * xx + se * randn(n2, 1); mu = M \ (A2' * y);
  hits = hits + mean(abs(xx - mu) <= 1.96 * sqrt(diag(Cpost))) / 600;
end
fprintf('  posterior mean and covariance equal the Tikhonov forms: %d; 95%% intervals contained the truth %.1f%% of the time\n', same, 100 * hits);
check(same && hits > 0.93 && hits < 0.97, 'Bayesian reading'); disp('  check passed: Tikhonov is the posterior mean');
disp('All checks passed.');
