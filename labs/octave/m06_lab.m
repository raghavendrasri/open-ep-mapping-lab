% m06 lab (GNU Octave / MATLAB) · Triangle meshes, Laplace-Beltrami operators and geodesics
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave with core functions only (sparse, eigs). It uses Octave's chained indexing
% f(x)(i); in MATLAB, replace it with temporary variables.
%
% This is the Octave copy of parts A-E of labs/python/m06_lab.ipynb (smaller meshes). Run with:  octave-cli m06_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
% The "check" lines pass with the code as given; if one fails after a change, that is information.

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);

% ------------------------------------------------------------------ meshes
t = (1 + sqrt(5)) / 2;
V0 = [-1 t 0; 1 t 0; -1 -t 0; 1 -t 0; 0 -1 t; 0 1 t; 0 -1 -t; 0 1 -t; t 0 -1; t 0 1; -t 0 -1; -t 0 1];
F0 = [0 11 5; 0 5 1; 0 1 7; 0 7 10; 0 10 11; 1 5 9; 5 11 4; 11 10 2; 10 7 6; 7 1 8; 3 9 4; 3 4 2; 3 2 6; 3 6 8; ...
      3 8 9; 4 9 5; 2 4 11; 6 2 10; 8 6 7; 9 8 1] + 1;
V0 = V0 ./ sqrt(sum(V0.^2, 2));
ico = cell(1, 5); ico{1} = {V0, F0};
for level = 1:4
  V = ico{level}{1}; F = ico{level}{2};
  E = unique(sort([F(:, [1 2]); F(:, [2 3]); F(:, [3 1])], 2), 'rows');
  M = (V(E(:, 1), :) + V(E(:, 2), :)) / 2; M = M ./ sqrt(sum(M.^2, 2));
  key = sparse(E(:, 1), E(:, 2), size(V, 1) + (1:size(E, 1))', size(V, 1), size(V, 1)); key = key + key';
  ab = full(key(sub2ind(size(key), F(:, 1), F(:, 2))));
  bc = full(key(sub2ind(size(key), F(:, 2), F(:, 3))));
  ca = full(key(sub2ind(size(key), F(:, 3), F(:, 1))));
  ico{level + 1} = {[V; M], [F(:, 1) ab ca; F(:, 2) bc ab; F(:, 3) ca bc; ab bc ca]};
end
edges_of = @(F) unique(sort([F(:, [1 2]); F(:, [2 3]); F(:, [3 1])], 2), 'rows');

% cotangent matrix and barycentric areas (eq-m06-cotan)
cotw = @(V, F, k) sum((V(F(:, mod(k, 3) + 1), :) - V(F(:, k), :)) .* (V(F(:, mod(k + 1, 3) + 1), :) - V(F(:, k), :)), 2) ...
       ./ sqrt(sum(cross(V(F(:, mod(k, 3) + 1), :) - V(F(:, k), :), V(F(:, mod(k + 1, 3) + 1), :) - V(F(:, k), :)).^2, 2));
offd = @(V, F) sparse([F(:, 2); F(:, 3); F(:, 3); F(:, 1); F(:, 1); F(:, 2)], [F(:, 3); F(:, 2); F(:, 1); F(:, 3); F(:, 2); F(:, 1)], ...
       0.5 * [cotw(V, F, 1); cotw(V, F, 1); cotw(V, F, 2); cotw(V, F, 2); cotw(V, F, 3); cotw(V, F, 3)], size(V, 1), size(V, 1));
cotan = @(V, F) offd(V, F) - spdiags(full(sum(offd(V, F), 2)), 0, size(V, 1), size(V, 1));
fareas = @(V, F) 0.5 * sqrt(sum(cross(V(F(:, 2), :) - V(F(:, 1), :), V(F(:, 3), :) - V(F(:, 1), :)).^2, 2));
vareas = @(V, F) accumarray(F(:), repmat(fareas(V, F) / 3, 3, 1), [size(V, 1), 1]);
lb = @(V, F, u) (cotan(V, F) * u) ./ vareas(V, F);
% per-face gradient (eq-m06-gradient)
fnorm = @(V, F) cross(V(F(:, 2), :) - V(F(:, 1), :), V(F(:, 3), :) - V(F(:, 1), :));
fgrad = @(V, F, u) (u(F(:, 1)) .* cross(fnorm(V, F) ./ sqrt(sum(fnorm(V, F).^2, 2)), V(F(:, 3), :) - V(F(:, 2), :)) ...
                  + u(F(:, 2)) .* cross(fnorm(V, F) ./ sqrt(sum(fnorm(V, F).^2, 2)), V(F(:, 1), :) - V(F(:, 3), :)) ...
                  + u(F(:, 3)) .* cross(fnorm(V, F) ./ sqrt(sum(fnorm(V, F).^2, 2)), V(F(:, 2), :) - V(F(:, 1), :))) ...
                  ./ sqrt(sum(fnorm(V, F).^2, 2));

% ------------------------------------------------------------------ Part A
disp('Part A: meshes');
for level = 0:4
  V = ico{level + 1}{1}; F = ico{level + 1}{2}; nE = size(edges_of(F), 1);
  fprintf('  level %d: V = %4d, E = %5d, F = %5d, V - E + F = %d\n', level, size(V, 1), nE, size(F, 1), size(V, 1) - nE + size(F, 1));
  check(size(V, 1) - nE + size(F, 1) == 2 && 2 * nE == 3 * size(F, 1), 'Euler characteristic 2');
end
disp('  check passed: V - E + F = 2 and E = 3F/2');

% lattice patch
n = 15; [ii, jj] = meshgrid(0:n-1, 0:n-1);
Vl = [reshape((ii + 0.5 * mod(jj, 2))', [], 1), reshape((jj * sqrt(3) / 2)', [], 1), zeros(n * n, 1)];
Fl = [];
for j = 0:n-2
  for i = 0:n-2
    a = j*n + i + 1; b = a + 1; c = a + n; d = c + 1;
    if mod(j, 2) == 0, Fl = [Fl; a b c; b d c]; else, Fl = [Fl; a b d; a d c]; end
  end
end

% ------------------------------------------------------------------ Part B
disp('Part B: gradients and conduction velocity');
rand('seed', 3); Vj = Vl; Vj(:, 1:2) = Vj(:, 1:2) + 0.25 * (2 * rand(n * n, 2) - 1);
dirv = [cos(0.7) sin(0.7) 0];
lat = (Vj * dirv') / 0.8;
g = fgrad(Vj, Fl, lat);
v = g ./ sum(g.^2, 2);
err = max(abs(sqrt(sum(v.^2, 2)) - 0.8));
fprintf('  planar wave at 0.8 mm/ms: largest speed error %.1e\n', err);
check(err < 1e-12, 'conduction velocity is exact for a planar wave'); disp('  check passed: exact velocity');

% ------------------------------------------------------------------ Part C
disp('Part C: the cotangent Laplacian');
inner = Vl(:, 1) > 2 & Vl(:, 1) < 10 & Vl(:, 2) > 2 & Vl(:, 2) < 10;
q = lb(Vl, Fl, Vl(:, 1).^2 + Vl(:, 2).^2); lin = lb(Vj, Fl, 2 * Vj(:, 1) - 3 * Vj(:, 2) + 1);
innerj = Vj(:, 1) > 2 & Vj(:, 1) < 10 & Vj(:, 2) > 2 & Vj(:, 2) < 10;
fprintf('  flat: linear %.1e; x^2 + y^2 on the lattice %.6f-%.6f (exact 4)\n', max(abs(lin(innerj))), min(q(inner)), max(q(inner)));
check(max(abs(lin(innerj))) < 1e-10 && max(abs(q(inner) - 4)) < 1e-10, 'flat checks'); disp('  check passed: flat patch');
med = zeros(1, 3);
for level = 2:4
  V = ico{level + 1}{1}; F = ico{level + 1}{2};
  e = abs(lb(V, F, V(:, 3)) + 2 * V(:, 3));
  med(level - 1) = median(e);
  fprintf('  sphere level %d: median error %.1e, worst %.2f\n', level, median(e), max(e));
end
check(med(3) < med(1) / 10, 'the typical error converges'); disp('  check passed: Laplacian of z tends to -2z');

% ------------------------------------------------------------------ Part D
disp('Part D: the spectrum of the sphere');
V = ico{4}{1}; F = ico{4}{2};
lam = sort(eigs(-cotan(V, F), spdiags(vareas(V, F), 0, size(V, 1), size(V, 1)), 9, -1e-6));
fprintf('  first nine eigenvalues: %s\n', mat2str(round(lam' * 1000) / 1000));
check(all(abs(lam(2:4) - 2) < 0.02) && all(abs(lam(5:9) - 6) < 0.1), 'l(l+1): 2 (x3), 6 (x5)'); disp('  check passed: 0, 2, 6');

% ------------------------------------------------------------------ Part E
disp('Part E: distances on a mesh');
% Dijkstra along edges on the unit sphere (level 3), simple O(V^2) version
V = ico{4}{1}; F = ico{4}{2}; E = edges_of(F); nv = size(V, 1);
W = sparse([E(:, 1); E(:, 2)], [E(:, 2); E(:, 1)], repmat(sqrt(sum((V(E(:, 1), :) - V(E(:, 2), :)).^2, 2)), 2, 1), nv, nv);
dist = inf(nv, 1); dist(1) = 0; done = false(nv, 1);
for it = 1:nv
  dd = dist; dd(done) = inf; [~, u] = min(dd); done(u) = true;
  [nb, ~, w] = find(W(:, u));
  dist(nb) = min(dist(nb), dist(u) + w);
end
exact = acos(max(min(V * V(1, :)', 1), -1));
% heat method (Crane et al. 2012), t = h^2
L = cotan(V, F); A = spdiags(vareas(V, F), 0, nv, nv);
h = mean(sqrt(sum((V(E(:, 1), :) - V(E(:, 2), :)).^2, 2)));
delta = zeros(nv, 1); delta(1) = 1;
u = (A - h^2 * L) \ delta;
gu = fgrad(V, F, u); X = -gu ./ sqrt(sum(gu.^2, 2));
divX = zeros(nv, 1);
for k = 1:3
  i = F(:, k); j = F(:, mod(k, 3) + 1); l = F(:, mod(k + 1, 3) + 1);
  e1 = V(j, :) - V(i, :); e2 = V(l, :) - V(i, :);
  cot_l = sum((V(i, :) - V(l, :)) .* (V(j, :) - V(l, :)), 2) ./ sqrt(sum(cross(V(i, :) - V(l, :), V(j, :) - V(l, :)).^2, 2));
  cot_j = sum((V(i, :) - V(j, :)) .* (V(l, :) - V(j, :)), 2) ./ sqrt(sum(cross(V(i, :) - V(j, :), V(l, :) - V(j, :)).^2, 2));
  divX = divX + accumarray(i, 0.5 * (cot_l .* sum(e1 .* X, 2) + cot_j .* sum(e2 .* X, 2)), [nv 1]);
end
Lp = L; Lp(1, :) = 0; Lp(1, 1) = 1; divX(1) = 0;
phi = Lp \ divX; phi = abs(phi - phi(1));
fprintf('  unit sphere, level 3: edge paths up to %.3f too long; heat method mean error %.4f\n', max(dist - exact), mean(abs(phi - exact)));
check(max(dist - exact) > 0.15 && mean(abs(phi - exact)) < 0.03, 'edge paths are biased; the heat method is close');
disp('  check passed: heat method beats edge paths');
th = linspace(0, pi/3, 7); r = (sin(th) + sin(pi/3 - th)) / sin(pi/3);
fprintf('  lattice edge-path ratio from 0 to 60 degrees: %s (max 2/sqrt(3) = %.4f)\n', mat2str(round(r * 1e4) / 1e4), 2 / sqrt(3));
check(abs(max(r) - 2 / sqrt(3)) < 1e-12, 'worst case 2/sqrt(3) at 30 degrees'); disp('  check passed: lattice formula');
if make_plots
  figure; plot(exact, dist, '.', exact, phi, '.'); xlabel('exact distance'); ylabel('computed'); legend('edge paths', 'heat method');
end
disp('All checks passed.');
