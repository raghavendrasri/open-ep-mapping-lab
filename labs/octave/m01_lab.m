% m01 lab (GNU Octave / MATLAB) · Bioelectric sources: transmembrane current, dipoles and double layers
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave or base MATLAB, no toolboxes.
%
% This is the Octave copy of parts A-E of labs/python/m01_lab.ipynb. Run with:  octave-cli m01_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
%
% Relative units: conductivity sigma = 1, beta = 1, dV = 1, distances in mm, as in m03.
% The "check" lines pass with the code as given; if one fails after a change, that is information.

% eq-m01-point: phi = I / (4 pi sigma r)
point_pot = @(I, sig, P, src) I ./ (4 * pi * sig * sqrt(sum((P - src).^2, 2)));
% eq-m01-dipole: phi = p . (r - r0) / (4 pi sigma |r - r0|^3)
dipole_pot = @(p, sig, P) (P * p(:)) ./ (4 * pi * sig * sqrt(sum(P.^2, 2)).^3);
pair_pot = @(I, d, sig, P) point_pot(I, sig, P, [0 0 d/2]) - point_pot(I, sig, P, [0 0 -d/2]);
% eq-m01-double-layer on the axis of a disk: Omega = 2 pi (1 - z / sqrt(z^2 + R^2)), signed by side
disk_omega_axis = @(R, z) sign(z) .* 2 * pi .* (1 - abs(z) ./ sqrt(z.^2 + R^2));
% the m03 arctangent front and eq-m01-core
front_vm = @(s, w) 0.5 - atan(s ./ w) / pi;
front_im = @(s, w) 2 * w .* s ./ (pi * (s.^2 + w^2).^2);
axial_i = @(s, w) w ./ (pi * (s.^2 + w^2));
% eq-m01-front-dipole: line of dipoles (moment p per unit length) at height h
line_dipole = @(p, sig, s, h) p .* s ./ (2 * pi * sig * (s.^2 + h^2));

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);

% ------------------------------------------------------------------ Part A
disp('Part A: a point source');
phi = @(P) point_pot(1, 1, P, [0 0 0]);
h = 1e-3; E = eye(3) * h;
pts = [1 0 0; 0.3 -2 1.5; 5 5 5];
worst = 0;
for k = 1:3
  p = pts(k, :);
  L = 0;
  for i = 1:3
    L = L + (phi(p + E(i, :)) - 2 * phi(p) + phi(p - E(i, :))) / h^2;
  end
  worst = max(worst, abs(L / phi(p)));
end
fprintf('  largest Laplacian / potential away from the source: %.1e\n', worst);
check(worst < 1e-4, 'the potential satisfies Laplace''s equation away from the source'); disp('  check passed: Laplace''s equation');
% current through a sphere of radius R: sigma * E_r * 4 pi R^2
for R = [0.5 2 10]
  flux = 1 * (1 / (4 * pi * R^2)) * 4 * pi * R^2;
  check(abs(flux - 1) < 1e-12, 'current is conserved');
end
disp('  check passed: the current through every sphere is I');

% ------------------------------------------------------------------ Part B
disp('Part B: from a source-sink pair to a dipole');
rho = logspace(-3, 3, 200)';
P = [zeros(size(rho)) zeros(size(rho)) 0.5 + rho];
lp = log(abs(pair_pot(1, 1, 1, P)));
slope = gradient(lp, log(rho));
fprintf('  falloff slope close to the pole %.3f, far away %.3f\n', slope(1), slope(end));
check(abs(slope(1) + 1) < 0.01 && abs(slope(end) + 2) < 0.01, 'monopole close up, dipole far away');
disp('  check passed: slopes -1 and -2');
pts = [0.3 0.2 5; 1 -2 0.5; 4 1 -3];
errs = zeros(1, 3); ds = [0.5 0.1 0.02];
for k = 1:3
  d = ds(k);
  errs(k) = max(abs(pair_pot(1 / d, d, 1, pts) ./ dipole_pot([0 0 1], 1, pts) - 1));
  fprintf('  separation %.2f mm: largest relative difference from the dipole %.2e\n', d, errs(k));
end
check(errs(3) < errs(2) && errs(2) < errs(1) && errs(3) < 1e-3, 'the pair tends to the dipole');
disp('  check passed: the pair tends to the dipole');

% ------------------------------------------------------------------ Part C
disp('Part C: a double layer and its solid angle');
R = 2; n = 400;
[RR, TT] = ndgrid(((1:n) - 0.5) * R / n, ((1:2 * n) - 0.5) * pi / n);
dA = RR * (R / n) * (pi / n);
X = RR .* cos(TT); Y = RR .* sin(TT);
z0 = 1.0;
r3 = sqrt(X.^2 + Y.^2 + z0^2).^3;
dipole_sum = sum(sum(dA .* z0 ./ (4 * pi * r3)));
formula = disk_omega_axis(R, z0) / (4 * pi);
fprintf('  on the axis at 1 mm: sum of dipoles %.5f, tau Omega / (4 pi sigma) %.5f\n', dipole_sum, formula);
check(abs(dipole_sum - formula) < 1e-5, 'a uniform double layer gives tau Omega / (4 pi sigma)');
disp('  check passed: tau Omega / (4 pi sigma)');
jump = (disk_omega_axis(R, 1e-6) - disk_omega_axis(R, -1e-6)) / (4 * pi);
fprintf('  jump across the layer: %.4f (tau / sigma = 1)\n', jump);
check(abs(jump - 1) < 1e-5, 'the potential jumps by tau / sigma across the layer');
disp('  check passed: jump of tau / sigma');

% ------------------------------------------------------------------ Part D
disp('Part D: membrane current across a wavefront');
s = linspace(-20000, 20000, 2000001);
for w = [0.1 0.3 1 3]
  im = front_im(s, w);
  net = trapz(s, im);
  pm = trapz(s, s .* im);
  fprintf('  width %.1f mm: net membrane current %+.1e, dipole moment %.4f\n', w, net, pm);
  check(abs(net) < 1e-9 && abs(pm - 1) < 2e-3, 'net current zero and dipole moment beta dV');
end
disp('  check passed: every front has net current zero and dipole moment beta dV');
fine = linspace(-5, 5, 20001);
i_num = -gradient(axial_i(fine, 0.3), fine);
check(max(abs(i_num - front_im(fine, 0.3))) < 1e-3 * max(abs(front_im(fine, 0.3))), 'i_m = -dI_i/dx');
disp('  check passed: i_m = -dI_i/dx');

% ------------------------------------------------------------------ Part E
disp('Part E: the wavefront as a line of dipoles');
w = 0.3; hh = 1.0;
ss = linspace(-8, 8, 33);
x = linspace(-4000, 4000, 800001); dx = x(2) - x(1);
imx = front_im(x, w);
quad = zeros(size(ss));
for k = 1:numel(ss)
  quad(k) = -sum(imx .* log((ss(k) - x).^2 + hh^2) / 2) * dx / (2 * pi);
end
closed = (1 / (2 * pi)) * ss ./ (ss.^2 + (w + hh)^2);
err_quad = max(abs(quad - closed)) / max(abs(closed));
err_line = max(abs(line_dipole(1, 1, ss, w + hh) - closed)) / max(abs(closed));
fprintf('  sum of strips vs m03 closed form %.1e; line of dipoles at height w + h vs closed form %.1e\n', err_quad, err_line);
check(err_quad < 1e-6 && err_line < 1e-12, 'a front of width w at height h is a line of dipoles at height w + h');
disp('  check passed: a front of width w at height h is a line of dipoles at height w + h');

if make_plots
  figure; plot(ss, closed, 'k-', ss, quad, 'o', ss, line_dipole(1, 1, ss, hh), '--');
  xlabel('s (mm)'); ylabel('potential (relative)');
  legend('m03 closed form', 'sum of strips', 'thin front at height h');
end
disp('All checks passed.');
