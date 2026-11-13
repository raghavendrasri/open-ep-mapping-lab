% m02 lab (GNU Octave / MATLAB) · Volume conduction and Poisson's equation
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave, no packages (it uses Octave's merge and chained indexing f(x)(idx); in
% MATLAB, replace those with temporary variables).
%
% This is the Octave copy of parts A-D of labs/python/m02_lab.ipynb. Run with:  octave-cli m02_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
%
% Relative units, distances in mm; conductivity ratios are parameters, not tissue values.
% The "check" lines pass with the code as given; if one fails after a change, that is information.

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);

% eq-m02-poisson: exact 2-D potential of a Gaussian source of total current 1 and width s (sigma = 1)
gauss_src = @(X, Y, s) exp(-(X.^2 + Y.^2) / (2 * s^2)) / (2 * pi * s^2);
gauss_pot = @(R, s) -(1 / (2 * pi)) * (log(R) + 0.5 * expint(R.^2 / (2 * s^2)));
% eq-m02-images (2-D): line source at (0, -d) in medium 1 (y < 0)
kref = @(s1, s2) (s1 - s2) / (s1 + s2);
% (each branch adds 1 inside its logarithms where the other branch applies, so no 0 * Inf appears)
img2 = @(s1, s2, d, X, Y) (Y <= 0) .* (-(1 / (2 * pi * s1)) * (log(hypot(X, Y + d) + (Y > 0)) + kref(s1, s2) * log(hypot(X, Y - d) + (Y > 0)))) ...
     + (Y > 0) .* (-(1 / (pi * (s1 + s2))) * log(hypot(X, Y + d) + (Y <= 0)));

% eq-m02-fd with anonymous functions only (so the file runs unchanged in Octave and MATLAB).
% Nodes are numbered column by column (meshgrid layout); D is the difference between neighbors, F the
% harmonic-mean face conductivity, and div(sigma grad phi) ~ -(Dx' Fx Dx + Dy' Fy Dy) phi / h^2.
Lsel = @(n) spdiags(ones(n - 1, 1), 0, n - 1, n);
Rsel = @(n) spdiags(ones(n - 1, 1), 1, n - 1, n);
hmean = @(a, b) 2 * a .* b ./ (a + b);
opx = @(ny, nx, s) kron(Rsel(nx) - Lsel(nx), speye(ny))' * spdiags(hmean(kron(Lsel(nx), speye(ny)) * s, kron(Rsel(nx), speye(ny)) * s), 0, ny * (nx - 1), ny * (nx - 1)) * kron(Rsel(nx) - Lsel(nx), speye(ny));
opy = @(ny, nx, s) kron(speye(nx), Rsel(ny) - Lsel(ny))' * spdiags(hmean(kron(speye(nx), Lsel(ny)) * s, kron(speye(nx), Rsel(ny)) * s), 0, (ny - 1) * nx, (ny - 1) * nx) * kron(speye(nx), Rsel(ny) - Lsel(ny));
edgemask = @(ny, nx) [true(1, nx); [true(ny - 2, 1) false(ny - 2, nx - 2) true(ny - 2, 1)]; true(1, nx)];
% Dirichlet rows replace the equations on the outer ring
solve_poisson = @(sig, src, h, bnd) reshape( ...
  (spdiags(double(~edgemask(size(sig, 1), size(sig, 2))(:)), 0, numel(sig), numel(sig)) * (opx(size(sig, 1), size(sig, 2), sig(:)) + opy(size(sig, 1), size(sig, 2), sig(:))) / h^2 ...
   + spdiags(double(edgemask(size(sig, 1), size(sig, 2))(:)), 0, numel(sig), numel(sig))) ...
  \ merge(edgemask(size(sig, 1), size(sig, 2))(:), bnd(:), src(:)), size(sig));
grid_x = @(n, half) repmat(linspace(-half, half, n), n, 1);
grid_y = @(n, half) repmat(linspace(-half, half, n)', 1, n);

% ------------------------------------------------------------------ Part A
disp('Part A: Poisson''s equation on a grid');
ns = [40 80 160]; errs = zeros(1, 3);
for q = 1:3
  X = grid_x(ns(q), 10); Y = grid_y(ns(q), 10); h = X(1, 2) - X(1, 1);
  R = hypot(X, Y); R(R == 0) = 1e-9;
  ex = gauss_pot(R, 1);
  phi = solve_poisson(ones(size(X)), gauss_src(X, Y, 1), h, ex);
  errs(q) = max(abs(phi(:) - ex(:)));
  fprintf('  %3d nodes per side: largest error %.2e\n', ns(q), errs(q));
end
ord = log2(errs(1:2) ./ errs(2:3));
fprintf('  observed order %.2f, %.2f\n', ord);
check(all(abs(ord - 2) < 0.2), 'the scheme is second-order accurate'); disp('  check passed: second order');

% ------------------------------------------------------------------ Part B
disp('Part B: a flat interface and the method of images');
img3 = @(s1, s2, d, P) (P(:, 3) <= 0) .* (1 ./ (4 * pi * s1) .* (1 ./ sqrt(sum((P - [0 0 -d]).^2, 2)) + kref(s1, s2) ./ sqrt(sum((P - [0 0 d]).^2, 2)))) ...
     + (P(:, 3) > 0) .* (1 ./ (2 * pi * (s1 + s2) * sqrt(sum((P - [0 0 -d]).^2, 2))));
for s2 = [0.25 4]
  e = 1e-6; hz = 1e-4;
  pb = img3(1, s2, 2, [0.7 0.3 -e]); pa = img3(1, s2, 2, [0.7 0.3 e]);
  jb = -1 * (img3(1, s2, 2, [0.7 0.3 -e]) - img3(1, s2, 2, [0.7 0.3 -e-hz])) / hz;
  ja = -s2 * (img3(1, s2, 2, [0.7 0.3 e+hz]) - img3(1, s2, 2, [0.7 0.3 e])) / hz;
  fprintf('  sigma2 = %.2f: potential mismatch %.1e, normal-current mismatch %.1e\n', s2, abs(pa - pb) / pb, abs(ja - jb) / abs(jb));
  check(abs(pa - pb) / pb < 1e-4 && abs(ja - jb) / abs(jb) < 1e-2, 'potential and normal current are continuous');
end
disp('  check passed: continuity of potential and normal current');
ins = img3(1, 1e-12, 2, [0.4 -0.2 1]) / (1 / (4 * pi * norm([0.4 -0.2 3])));
fprintf('  insulating medium 2 multiplies the potential by %.3f\n', ins);
check(abs(ins - 2) < 1e-6, 'an insulating boundary doubles the potential'); disp('  check passed: doubling');

% ------------------------------------------------------------------ Part C
disp('Part C: two media on a grid');
tm_src = @(X, Y) exp(-(X.^2 + (Y + 2).^2) / (2 * 0.3^2)) / (2 * pi * 0.3^2);
tm_phi = @(n, s2) solve_poisson(1 + (s2 - 1) * (grid_y(n, 10) > 0), tm_src(grid_x(n, 10), grid_y(n, 10)), 20 / (n - 1), img2(1, s2, 2, grid_x(n, 10), grid_y(n, 10)));
tm_far = @(n) hypot(grid_x(n, 10), grid_y(n, 10) + 2) > 2;
two_media = @(n, s2) max(abs(tm_phi(n, s2)(tm_far(n)) - img2(1, s2, 2, grid_x(n, 10), grid_y(n, 10))(tm_far(n))));
ef = [two_media(80, 3) two_media(160, 3)];
en = [two_media(81, 3) two_media(161, 3)];
fprintf('  interface on faces: order %.2f; on nodes: order %.2f\n', log2(ef(1) / ef(2)), log2(en(1) / en(2)));
check(log2(ef(1) / ef(2)) > 1.8 && log2(en(1) / en(2)) < 1.3, 'interface placement decides the order');
disp('  check passed: second order on faces, first order on nodes');

% ------------------------------------------------------------------ Part D
disp('Part D: reciprocity and lead fields');
p = [0.3 -0.5 1]; s2 = 4; d = 2; el = [1 0.5 1.5]; ep = 1e-5;
u = p / norm(p) * ep / 2;
srcpot = @(P, src) (P(3) <= 0) * (1 / (4 * pi) * (1 / norm(P - src) + kref(1, s2) / norm(P - [src(1:2) -src(3)]))) ...
                 + (P(3) > 0) * (1 / (2 * pi * (1 + s2) * norm(P - src)));
direct = norm(p) * (srcpot(el, [0 0 -d] + u) - srcpot(el, [0 0 -d] - u)) / ep;
% reciprocity: inject unit current at the electrode (medium 2), potential psi at the source (medium 1)
psi = @(P) 1 / (2 * pi * (s2 + 1) * norm(P - el));        % seen from medium 1 (below)
g = zeros(1, 3); E3 = eye(3);
for i = 1:3
  g(i) = (psi([0 0 -d] + ep * E3(i, :)) - psi([0 0 -d] - ep * E3(i, :))) / (2 * ep);
end
recip = dot(p, g);
fprintf('  direct %.6f, by reciprocity %.6f\n', direct, recip);
check(abs(direct - recip) < 1e-5 * abs(direct), 'reciprocity holds across the interface'); disp('  check passed: reciprocity');
depth = linspace(0.2, 8, 100)';
lead = @(e, P) -(P - e) ./ (4 * pi * sqrt(sum((P - e).^2, 2)).^3);
P = [0 * depth 0 * depth -depth];
uni = sqrt(sum(lead([1 0 1], P).^2, 2));
bi = sqrt(sum((lead([1 0 1], P) - lead([-1 0 1], P)).^2, 2));
fprintf('  sensitivity at 8 mm against 0.2 mm: unipolar %.1e, bipole %.1e\n', uni(end) / uni(1), bi(end) / bi(1));
check(bi(end) / bi(1) < uni(end) / uni(1), 'a bipole''s lead field falls faster with depth'); disp('  check passed: bipole sees shallower');
if make_plots
  figure; semilogy(depth, uni / uni(1), depth, bi / bi(1)); xlabel('depth (mm)'); ylabel('relative sensitivity');
  legend('unipolar', 'bipole');
end
disp('All checks passed.');
