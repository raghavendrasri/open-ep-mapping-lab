% m03 lab (GNU Octave / MATLAB) · Unipolar, bipolar and omnipolar electrograms
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave or base MATLAB, no toolboxes.
%
% This is the Octave copy of parts A-D of labs/python/m03_lab.ipynb. Part E (real PhysioNet
% data) is in the Python notebook only. Run with:  octave-cli m03_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
%
% Units: mm, ms, conduction velocity in mm/ms (= m/s). Potentials in relative units.
% The "check" lines pass with the code as given; if one fails after a change, that is information.

% Model functions (anonymous, so the file runs unchanged in Octave and MATLAB).
% U(s) = A s / (s^2 + a^2), a = w + h  (eq-m03-unipolar-closed)
unipolar = @(s, a, A) A .* s ./ (s.^2 + a.^2);
% U(s + delta) - U(s - delta), delta = (d/2) cos(theta)  (eq-m03-bipolar-planar)
bipolar_planar = @(s, d, theta, a, A) unipolar(s + 0.5 * d * cos(theta), a, A) - unipolar(s - 0.5 * d * cos(theta), a, A);
% Least-squares field from a clique's bipoles: E = -(D D')^-1 D b  (eq-m03-clique-field)
% P: m x 2 positions; U: m x nt signals; pairs: p x 2 rows [i j], bipole b = phi_j - phi_i.
sep = @(P, pairs) (P(pairs(:, 2), :) - P(pairs(:, 1), :))';
bip = @(U, pairs) U(pairs(:, 2), :) - U(pairs(:, 1), :);
clique_field = @(P, U, pairs) -((sep(P, pairs) * sep(P, pairs)') \ (sep(P, pairs) * bip(U, pairs)));
ptp = @(v) max(v) - min(v);

make_plots = isempty(getenv('EPML_NO_PLOTS'));

% ------------------------------------------------------------------ Part A
disp('Part A: the unipolar electrogram from first principles');

w = 0.3; h = 1.0;                 % front width and electrode height, mm (m03 defaults)
beta = 1; sigma = 1; dV = 1;      % relative units
A = beta * dV / (2 * pi * sigma);
a = w + h;

% membrane current i_m = beta d2Vm/dx2 for the arctangent front, front at x = 0
x = linspace(-2000, 2000, 400001);
dx = x(2) - x(1);
im = beta * dV * 2 * w .* x ./ (pi * (x.^2 + w^2).^2);

% volume-conductor integral over a sheet |y| < Y, with the y-integral done exactly
Y = 1e5;
s = linspace(-8, 8, 33);
phi_num = zeros(size(s));
for i = 1:numel(s)
  r = sqrt((s(i) - x).^2 + h^2);
  phi_num(i) = sum(im .* 2 .* asinh(Y ./ r)) * dx / (4 * pi * sigma);
end
phi_closed = unipolar(s, a, A);
err = max(abs(phi_num - phi_closed)) / max(abs(phi_closed));
fprintf('  largest difference between quadrature and closed form: %.1e of the peak\n', err);
assert(err < 1e-3, 'closed form matches the volume-conductor integral'); fprintf('  check passed: %s\n', 'closed form matches the volume-conductor integral');

c = 1.0;                                  % m/s = mm/ms
t = linspace(-15, 15, 3001);              % ms
U = unipolar(-c * t, a, A);
dUdt = gradient(U, t);
[~, k] = min(dUdt);
t_steep = t(k);
fprintf('  steepest downstroke at %+.3f ms (true activation at 0 ms)\n', t_steep);
assert(abs(t_steep) <= t(2) - t(1), 'steepest downstroke marks activation in ideal propagation'); fprintf('  check passed: %s\n', 'steepest downstroke marks activation in ideal propagation');

heights = [0.25 0.5 1 2 4];
p2p = zeros(size(heights));
for i = 1:numel(heights)
  u = unipolar(-c * t, w + heights(i), A);
  p2p(i) = max(u) - min(u);
end
coef = polyfit(log(w + heights), log(p2p), 1);
fprintf('  log-log slope of peak-to-peak versus (w + h): %.3f (theory: -1)\n', coef(1));
assert(abs(coef(1) + 1) < 0.01, 'unipolar amplitude falls as 1/(w + h)'); fprintf('  check passed: %s\n', 'unipolar amplitude falls as 1/(w + h)');

if make_plots
  figure; plot(s, phi_closed, '-', s, phi_num, 'o');
  xlabel('s: distance from front to electrode (mm)'); ylabel('U (relative units)');
  legend('closed form', 'direct quadrature'); title('Unipolar potential versus front position');
  figure; plot(t, U, '-', t_steep, U(k), 'o'); hold on; plot([0 0], ylim, '--k');
  xlabel('time (ms)'); ylabel('U (relative units)'); title('Unipolar electrogram and its steepest downstroke');
end

% ------------------------------------------------------------------ Part B
disp('Part B: rotating a bipole');

s_long = linspace(-80, 80, 16001);
thetas = (0:5:180) * pi / 180;
ratio = @(d) arrayfun(@(th) max(bipolar_planar(s_long, d, th, a, A)) - min(bipolar_planar(s_long, d, th, a, A)), thetas) ...
             / (max(bipolar_planar(s_long, d, 0, a, A)) - min(bipolar_planar(s_long, d, 0, a, A)));
dev_small = max(abs(ratio(0.2) - abs(cos(thetas))));
dev_large = max(abs(ratio(2.0) - abs(cos(thetas))));
fprintf('  largest deviation from |cos theta|: %.4f at d = 0.2 mm, %.3f at d = 2 mm\n', dev_small, dev_large);
assert(dev_small < 0.01, 'close bipole follows |cos theta|'); fprintf('  check passed: %s\n', 'close bipole follows |cos theta|');
assert(dev_large > dev_small, 'the |cos theta| rule degrades as spacing grows'); fprintf('  check passed: %s\n', 'the |cos theta| rule degrades as spacing grows');

if make_plots
  figure; plot(thetas * 180 / pi, ratio(0.2), thetas * 180 / pi, ratio(2.0), thetas * 180 / pi, abs(cos(thetas)), '--k');
  xlabel('bipole angle theta (degrees)'); ylabel('peak-to-peak / aligned bipole');
  legend('d = 0.2 mm', 'd = 2 mm', '|cos theta|'); title('Bipolar amplitude versus orientation');
end

% ------------------------------------------------------------------ Part C
disp('Part C: recordings as spatial filters, with FFTs');

L = 4096; n = 2^16;
xg = ((0:n-1) - n/2) * (L / n);
kk = 2 * pi * [0:n/2-1, -n/2:-1] / L;                   % same order as fft output
im_g = beta * dV * 2 * w .* xg ./ (pi * (xg.^2 + w^2).^2);
im_hat = fft(ifftshift(im_g));
g = zeros(size(kk));
nz = kk ~= 0;
g(nz) = exp(-abs(kk(nz)) * h) ./ (2 * sigma * abs(kk(nz)));
phi_h = fftshift(real(ifft(im_hat .* g)));
win = abs(xg) < 20;
fft_err = max(abs(phi_h(win) - unipolar(xg(win), a, A))) / (max(phi_h) - min(phi_h));
fprintf('  FFT route versus closed form: largest difference %.1e of peak-to-peak\n', fft_err);
assert(fft_err < 1e-3, 'height filter exp(-|k| h) reproduces the closed form'); fprintf('  check passed: %s\n', 'height filter exp(-|k| h) reproduces the closed form');

d = 2.0;
direct = interp1(xg, phi_h, xg + d/2, 'linear', 0) - interp1(xg, phi_h, xg - d/2, 'linear', 0);
H = 2i * sin(kk * d / 2);
via_fft = fftshift(real(ifft(fft(ifftshift(phi_h)) .* H)));
mismatch = max(abs(direct(win) - via_fft(win))) / (max(direct) - min(direct));
fprintf('  bipole in space versus filter in frequency: largest mismatch %.1e\n', mismatch);
assert(mismatch < 1e-9, 'a bipole equals multiplying the spectrum by 2i sin(k d / 2)'); fprintf('  check passed: %s\n', 'a bipole equals multiplying the spectrum by 2i sin(k d / 2)');

% ------------------------------------------------------------------ Part D
disp('Part D: fields, cliques and omnipoles');

tD = linspace(-40, 40, 4001);
pairs = [1 2; 3 4; 1 3; 2 4; 1 4; 2 3];
spread = zeros(1, 5);
ds = [0.25 0.5 1 2 4];
for j = 1:numel(ds)
  d = ds(j);
  P = [0 0; d 0; 0 d; d d] - d/2;
  p2p_omni = zeros(1, 18);
  for q = 1:18
    th = 10 * (q - 1) * pi / 180;
    nvec = [cos(th); sin(th)];
    Uc = unipolar(P * nvec - c * tD, a, A);              % 4 x nt (implicit expansion)
    E = clique_field(P, Uc, pairs);
    [V, L2] = eig(E * E');
    [~, imax] = max(diag(L2));
    omega = V(:, imax);
    v = -d * (omega' * E);
    p2p_omni(q) = max(v) - min(v);
  end
  spread(j) = max(p2p_omni) / min(p2p_omni) - 1;
  fprintf('  d = %.2f mm (d/a = %.2f): omnipole varies by %.1f%% across directions\n', d, d / a, 100 * spread(j));
end
assert(spread(1) < 0.02, 'with spacing well below w + h the omnipole is nearly direction-independent'); fprintf('  check passed: %s\n', 'with spacing well below w + h the omnipole is nearly direction-independent');
assert(all(diff(spread) > 0), 'the spread grows with spacing'); fprintf('  check passed: %s\n', 'the spread grows with spacing');

d = 0.25;
P = [0 0; d 0; 0 d; d d] - d/2;
nvec = [cos(40 * pi / 180); sin(40 * pi / 180)];
for c_true = [0.5 1.0 1.5]
  Uc = unipolar(P * nvec - c_true * tD, a, A);
  E = clique_field(P, Uc, pairs);
  dudt = gradient(mean(Uc, 1), tD);
  En = nvec' * E;
  c_est = (max(dudt) - min(dudt)) / (max(En) - min(En));
  fprintf('  true c = %.2f m/s, estimated from one clique = %.3f m/s\n', c_true, c_est);
  assert(abs(c_est - c_true) / c_true < 0.02, 'conduction velocity from the amplitude ratio'); fprintf('  check passed: %s\n', 'conduction velocity from the amplitude ratio');
end

disp('All checks passed.');
